# Variable-length video generation (extend a single shot, or storyboard a complex one)

**Status: proposed, not yet implemented.** Written during a planning session on
2026-09-17; see also the published plan doc at
https://claude.ai/artifact/8s1Si9G33N1kycAdA9wvnZ for the same content in a
more readable layout.

## Context

Video generation is currently capped at a flat 5 seconds — not a real Luma limit,
just a single hardcoded module constant (`luma.VIDEO_DURATION_SECONDS = 5.0`) that
every video variant uses unconditionally. The user wants campaigns to be able to run
longer when the user or the concept calls for it, with two distinct mechanisms
matching how the request was framed:

- **A long, simple shot** (one continuous scene — product rotating, a slow push-in)
  should just get more time from its one starting image.
- **A genuinely complex idea** (a short story/sequence) should have Claude plan a
  storyboard — a few distinct scenes, each generated from its own starting image —
  stitched into one video, with a single voiceover/music pass over the assembled
  whole, not per-scene audio.

Today's pipeline is rigid 1:1:1:1:1: one `variants` row = one `image_prompt` = one
`motion_prompt` = one Luma job = one 5s `video_url`. Audio is already
duration-*parametric* under the hood (`llm.write_audio_script(..., duration_seconds)`,
`elevenlabs_music.generate_music(..., length_ms)` both already take an explicit
length) — they're just always fed the same constant today, so the audio side needs
almost no new work, only real wiring changes are in image/video generation.

**Design decision**: both tracks are the same underlying problem — "N ≥ 1 Luma
segments, assembled into one video, with exactly one audio pass over the total" —
so one mechanism serves both, distinguished by a `shot_kind` flag. This avoids
building two parallel systems. Everything below is additive: a variant that doesn't
ask for extra duration takes the exact same code path as today, unchanged.

## Part 0 — Schema (`supabase/migrations/0021_variable_length_video.sql`)

```sql
-- 'single' = today's exact behavior (no variant_shots rows, one Luma call, 5s) —
-- the default, so every existing/simple campaign is unaffected.
alter table variants add column if not exists assembly_mode text not null default 'single';
alter table variants add constraint variants_assembly_mode_check
  check (assembly_mode in ('single', 'extended', 'storyboard'));
alter table variants add column if not exists total_duration_seconds numeric;
  -- null under 'single' (implicitly VIDEO_DURATION_SECONDS); the real, post-clamp
  -- total otherwise — this is what audio gets budgeted to.

-- One row per Luma segment. 'extended_segment' = same scene, sliced motion, to
-- extend duration. 'storyboard_shot' = distinct scene, own starting image.
create table if not exists variant_shots (
  id uuid primary key default gen_random_uuid(),
  variant_id uuid not null references variants(id) on delete cascade,
  shot_index int not null,
  shot_kind text not null check (shot_kind in ('extended_segment', 'storyboard_shot')),
  scene_description text,        -- storyboard only; null for extended segments
  image_prompt text,             -- storyboard only: this shot's own image-gen prompt
  motion_prompt text not null,
  shot_duration_seconds numeric not null,
  image_url text,                -- storyboard only; extended reuses the variant's own image
  video_gen_job_id text,
  video_url text,                -- this shot's own raw silent segment
  generation_status text not null default 'pending'
    check (generation_status in ('pending', 'generating_image', 'generating_video', 'generated', 'failed')),
  video_gen_error text,
  created_at timestamptz not null default now(),
  unique (variant_id, shot_index)
);

alter table variant_shots enable row level security;
-- Mirror the existing ownership-via-campaign RLS pattern already used for
-- variants/captions (see 0001_init.sql) — same join-through-campaign shape, applied
-- to variant_shots via variant_id -> variants.campaign_id -> campaigns.user_id.
```

Why a child table instead of a jsonb array on `variants`: each shot needs its own
async job id/status/error, polled independently and updated concurrently — exactly
the case this codebase already reserves real relational tables for (`captions` is a
child table of `variants`; jsonb is reserved for conversational/free-form data like
`content_plan`/`scope_conversation`). A jsonb array would need read-modify-write
under concurrent pollers, which is exactly what a table with `unique (variant_id,
shot_index)` avoids for free.

## Part 1 — Scoping only captures the number, not the "how"

**`apps/api/app/services/llm.py`**, `continue_campaign_scoping`'s `finalize_tool`
schema: add one optional field per item —

```python
"duration_seconds": {
    "type": "integer", "minimum": 5, "maximum": 60,
    "description": "Only meaningful when media_type is 'video'. Set ABOVE the default "
    "(5s) only when the user explicitly asks for a longer video, or the concept clearly "
    "needs more time to tell. Do not proactively suggest a longer duration yourself — "
    "same restraint as web_search, only reach for it when actually warranted.",
},
```

Right after the tool call returns, next to the existing forced `include_music`
line — never trust the LLM's number alone:

```python
MAX_TOTAL_VIDEO_SECONDS = 60  # MVP cap
for item in items:
    item["include_music"] = item.get("media_type") == "video"
    item["duration_seconds"] = (
        max(5, min(int(item["duration_seconds"]), MAX_TOTAL_VIDEO_SECONDS))
        if item.get("media_type") == "video" and item.get("duration_seconds") else None
    )
```

Scoping stops here deliberately — deciding *single continuous shot* vs *storyboard*
needs the worked-out `image_prompt`, which doesn't exist yet at scoping time
(`concept` is one line, not a shot). That decision belongs in ideation (Part 2).

Thread it through `_expand_content_plan` (`step2_variants.py`) into each spec as
`duration_seconds` (default `None` = today's behavior), and add a small `"Xs"` badge
next to the existing count/platform/audio badges on the scope page's plan-item card
(`apps/web/app/campaign/[id]/scope/page.tsx`) — read-only, consistent with every
other field there.

## Part 2 — Ideation decides Track A vs Track B: new `llm.plan_video_shots`

**`apps/api/app/services/luma.py`**: add the assumed per-call ceiling as its own
constant (flagged the same way this file already flags its inline-base64 size
caveat — **confirm against `docs.agents.lumalabs.ai` during implementation**, not
fully nailed down by research alone):

```python
VIDEO_DURATION_SECONDS = 5.0        # unchanged legacy default, 'single' mode
SINGLE_SHOT_MAX_SECONDS = 10.0      # assumed per-call ceiling — CONFIRM against live docs
```

Generalize `submit_image_to_video(image_bytes, motion_prompt, *, content_type=...,
duration_seconds: float = VIDEO_DURATION_SECONDS)` — existing callers keep working
via the default; new callers pass a real per-shot duration.

**`llm.py`** — new function, same forced-tool-call shape as `ideate_motion_prompt`,
called only when `duration_seconds > luma.VIDEO_DURATION_SECONDS` (i.e. the user
actually asked for more than the default):

```python
MAX_SHOTS_PER_VARIANT = 6  # bounds per-variant Luma/image-gen fan-out (cost control)

def plan_video_shots(*, angle, image_prompt, brand_profile, product_profile,
                      campaign_type, concept, duration_seconds) -> tuple[dict, int]:
    """Decides HOW to reach the requested duration: 'extended' (one continuous scene,
    just longer — every segment repeats the SAME starting image, motion_prompt sliced
    into a continuous progression, e.g. seg1 'push-in begins' / seg2 'push-in
    continues, now close on product') or 'storyboard' (distinct scenes — only when one
    continuous shot genuinely can't carry the duration). Prefer 'extended' by default.
    Returns {"assembly_mode": "extended"|"storyboard", "shots": [{scene_description,
    motion_prompt, duration_seconds}, ...]}, each shot 3-10s, summing to ~the target,
    capped at MAX_SHOTS_PER_VARIANT shots."""
```

**`step2_variants.py`**, `ideate_variants` (video branch): after the existing
`ideate_motion_prompt` call, if `spec["duration_seconds"] > luma.VIDEO_DURATION_SECONDS`,
call `plan_video_shots`, clamp every returned shot duration server-side (`max(3.0,
min(duration, luma.SINGLE_SHOT_MAX_SECONDS))` — same defensive-clamp discipline as
`elevenlabs_music.py`'s `clamped_length`), compute `total_duration = sum(shot
durations)`, store `assembly_mode`/`total_duration_seconds` on the variant row, and
insert one `variant_shots` row per shot immediately (cheap — no media generated yet,
so review-before-spend is untouched). Wire `write_audio_script(...,
duration_seconds=total_duration or luma.VIDEO_DURATION_SECONDS)` and the equivalent
music `length_ms` — both already accept this, it's a one-line change each.

## Part 3 — Generation: shared execution for both tracks

**`step2_variants.py`**, `_generate_media_for_variant`: after the existing
image-gen + quality-check loop, branch on `variant["assembly_mode"]`. `'single'`
calls today's unchanged `_start_video_generation`. `'extended'`/`'storyboard'` call
new `_start_multi_shot_generation`, which for each `variant_shots` row:
- `extended_segment` — reuses the variant's own already-generated,
  already-quality-checked image bytes directly (no extra image-gen cost — the whole
  point of Track A staying cheap).
- `storyboard_shot` — needs its own starting image first. Extract the existing
  `MAX_QUALITY_RETRIES` retry loop out of `_generate_media_for_variant` into a shared
  helper `_generate_quality_checked_image(...)` (pure refactor, no behavior change)
  so both the single-image path and each storyboard shot call the identical loop
  instead of duplicating it.

Each shot then calls `luma.submit_image_to_video(shot_image_bytes,
shot["motion_prompt"], duration_seconds=shot["shot_duration_seconds"])`
independently and in parallel, storing its own `video_gen_job_id` and scheduling its
own poll via a new `schedule_shot_generation_poll(shot_id)` in `scheduler.py`
(exact sibling of the existing `schedule_video_generation_poll`).

**New `poll_shot_generation_job(shot_id, deadline_iso)`** in `step2_variants.py` —
near-copy of `poll_video_generation_job`, targeting `variant_shots` instead of
`variants`, with two real differences: (1) on completion it uploads the shot's own
*raw silent* segment and stops — no audio muxing per shot, that happens once, later,
on the assembled whole; (2) after marking a shot `generated`, it must find out
whether it was the *last* sibling to finish, and if so trigger assembly exactly
once. **Race to guard against**: two shots can complete in the same poll tick from
independent scheduler jobs, and both could see "all siblings done" simultaneously.
Guard with an atomic claim before assembling — e.g.
`UPDATE variants SET generation_status='assembling' WHERE id=:id AND
generation_status='generating'` — only the caller whose UPDATE actually affects a
row proceeds to `_assemble_and_finish_variant`; the other returns immediately. A
shot reaching `failed` is treated as **fatal for the whole variant** (unlike audio's
non-fatal "ship what you can" pattern) — a storyboard/extended video missing a scene
isn't a usable deliverable, so this deliberately breaks from that convention rather
than silently reusing it.

**New `apps/api/app/services/video_mix.py`** — same subprocess-wrapper style as
`audio_mix.py`: `concat_videos(segment_bytes: list[bytes]) -> bytes` using ffmpeg's
concat demuxer with `-c copy` (stream copy, no re-encode — safe since every segment
comes from the same Luma model/resolution/encoding). Note as a contingency, not a
blocker: if real Luma outputs ever turn out not stream-copy-compatible, fall back to
`-c:v libx264 -c:a aac` (re-encode, slower but always safe).

**`_assemble_and_finish_variant(client, variant_id)`** — downloads every shot's
segment in `shot_index` order, `video_mix.concat_videos` (or passes through directly
if only one shot), then runs the *existing* `_generate_and_mux_audio` exactly once
against the assembled silent video (budgeted to `total_duration_seconds`), and
finishes the variant identically to how `poll_video_generation_job`'s `'single'`
path does today (`_upload_variant_video`, set `video_url`/`generation_status`,
non-fatal `audio_gen_error` if only audio fails).

One-line change inside the existing `_generate_and_mux_audio`'s music call: budget
to `variant.get("total_duration_seconds") or luma.VIDEO_DURATION_SECONDS` instead of
the constant.

**Track A mechanism, both possibilities addressed as raised**: build the safe
fallback first — every segment re-seeds from the identical starting image, differing
only in a Claude-written continuous-progression `motion_prompt`. Real limitation,
stated plainly: since each segment starts from the same frame, concatenation can
show a visible "snap" at each boundary rather than perfectly seamless motion —
acceptable for a first version, not perfect. True frame-to-frame continuation (each
segment starting from the *previous segment's actual last frame*, if Luma's Agents
API supports supplying a prior generation's end frame as the next `start_frame`) is
a real possible upgrade but **unconfirmed in this codebase today** — gate it behind
a disabled-by-default `settings.luma_frame_continuation_enabled` config flag and
leave it as a documented follow-up rather than blocking this plan on confirming it
against Luma's live docs now.

## Part 4 — Frontend: review-before-spend for multi-shot variants

The core product guarantee — nothing expensive generates before the user reviews
and confirms prompts on `/campaign/[id]/prompts` — must hold identically for
multi-shot variants.

- **`schemas.py`**: `VariantOut` gains `assembly_mode`, `total_duration_seconds`,
  `shots: list[VariantShotOut] | None`. New `VariantShotOut`/`VariantShotUpdate`.
- **`routers/campaigns.py`**: `list_variants` batch-fetches `variant_shots` for the
  campaign's variants (avoid N+1) and nests them onto each `VariantOut`. New `PATCH
  /{campaign_id}/variants/{variant_id}/shots/{shot_id}` — same
  `awaiting_prompt_review`-only edit-window guard as the existing prompt PATCH.
- **`prompts/page.tsx`**: when `assembly_mode !== "single"`, render a header
  ("Extended — 20s across 3 segments" / "Storyboard — 20s across 4 shots") and each
  shot as a nested sub-card — `scene_description` editable for storyboard shots,
  `motion_prompt` editable for every shot, `shot_duration_seconds` as a small number
  input — same pattern as the existing `EditablePrompt` component, one level deeper,
  each shot saving independently to its own PATCH endpoint. `'single'`-mode variants
  render pixel-identical to today — zero UI change for the common case. MVP scope is
  edit-in-place only, no add/remove-shot control (that would need re-running
  `plan_video_shots`) — a clean, non-blocking follow-up.

## MVP defaults (all adjustable constants, none blocking)

| Constant | Value | Where |
|---|---|---|
| `VIDEO_DURATION_SECONDS` | 5.0 | `luma.py` — unchanged, `'single'` mode |
| `SINGLE_SHOT_MAX_SECONDS` | 10.0 | `luma.py` — **confirm vs. live Luma docs** |
| `MAX_TOTAL_VIDEO_SECONDS` | 60 | `llm.py` scoping clamp |
| `MAX_SHOTS_PER_VARIANT` | 6 | `llm.py` — cost/fan-out control |
| min shot duration | 3.0s | ideation clamp, mirrors ElevenLabs' own floor |
| `luma_frame_continuation_enabled` | `False` | `config.py`, new setting — gates the real-continuation upgrade |

Worth a one-line mention in the scoping system prompt (not a full cost estimate,
which stays on the existing backlog) that a longer/storyboard video costs more, so
the plan `summary` Claude shows the user can say e.g. "3-shot storyboard" rather
than silently multiplying spend.

## Verification

1. Compile-check + boot-check after each part.
2. Part 1: ask for a 20s video in scoping — confirm `content_plan` item gets
   `duration_seconds: 20` (and gets clamped if asked for e.g. 200).
3. Part 2: confirm ideation produces `assembly_mode` + `variant_shots` rows with
   prompts filled in and no media yet — no image/video-gen cost, campaign still
   lands in `awaiting_prompt_review` as today.
4. Part 3: generate one Track A (extended) variant end-to-end — confirm all shot
   polls resolve, assembly fires exactly once (not duplicated), final video plays as
   one continuous concatenated clip with exactly one audio pass sized to the real
   total. Force one shot to fail — confirm the whole variant flips to `failed`
   (fatal, not silently partial). Then one Track B (storyboard) variant — confirm
   each shot got its own distinct generated+quality-checked image.
5. Part 4: confirm a multi-shot variant's shots render and are editable before
   "Generate selected," and that a `'single'`-mode variant's UI is unchanged from
   today.
6. Regression: run one plain campaign with no `duration_seconds` requested,
   end-to-end — confirm `assembly_mode='single'`, no `variant_shots` rows, identical
   output to pre-change behavior.

### Critical files
- `supabase/migrations/0021_variable_length_video.sql` (new)
- `apps/api/app/services/luma.py` — `SINGLE_SHOT_MAX_SECONDS`, parametric duration
- `apps/api/app/services/llm.py` — new `plan_video_shots`, scoping `duration_seconds`
- `apps/api/app/pipeline/step2_variants.py` — shot planning, `_generate_quality_checked_image`
  extraction, `_start_multi_shot_generation`, `poll_shot_generation_job`,
  `_assemble_and_finish_variant`
- `apps/api/app/services/video_mix.py` (new)
- `apps/api/app/services/scheduler.py` — `schedule_shot_generation_poll`
- `apps/api/app/models/schemas.py`, `apps/api/app/routers/campaigns.py` — shot schema/endpoint
- `apps/web/app/campaign/[id]/prompts/page.tsx` — per-shot editable review UI
