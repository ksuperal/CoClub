# TODO

## Feedback / analytics (Step 5)

- [x] Real graph (`MetricsChart.tsx`), markdown-rendered report, and an ML
      best-posting-time recommendation (`services/posting_time.py`, RidgeCV)
      gated behind 10+ real posts with data.
- [ ] **Ads/boost integration** — Meta's Marketing API is separate from the
      organic Graph API already built. Staged plan: (1) now — deep-link the
      report's suggested variant into Meta's native "Boost Post" flow, no
      money touches CoClub; (2) later — `ads_read` for real cost/reach numbers
      in the recommendation; (3) `ads_management` (CoClub spending on the
      customer's behalf) — probably never, liability/UX cost too high for
      what it adds over (1).

## Video generation + posting

- [x] Image-to-video via Luma (`ray-3.2`), muxed with audio via ffmpeg,
      posted natively to Facebook/Instagram Reels/TikTok. Migrations
      `0006`-`0008` applied; `LUMA_API_KEY`/`ELEVENLABS_API_KEY`/ffmpeg all
      configured.
- [ ] **TikTok video posting untested end-to-end** — same domain-verification
      prerequisite as the photo path should carry over, unconfirmed live.
- [ ] Luma's inline-base64 image upload (`services/luma.py`) has an
      unconfirmed size ceiling — fine for a typical ad-creative PNG, untested
      against the real limit. Fallback if it ever fails: Luma's Files API.
- [ ] No notification when a video finishes generating in the background —
      user has to revisit the page to see it's ready.

## Campaign scoping (conversational, embedded in the wizard)

Replaced the old fixed intake fields (variant_count/media_type/audio
toggles) with `/campaign/[id]/scope` — a short chat where the user describes
campaign size in their own words and Claude proposes a concrete, heterogeneous
**content plan** (per-group media type, target platform(s), audio, and a real
creative concept) for confirmation before anything is generated. Full history:
a general-purpose 17-tool standalone chat agent was built and deliberately
removed first (`docs/agent-migration-plan.md`, kept for the reasoning trail)
— it just re-asked the wizard's own questions via chat with no real
advantage; this is what replaced it.

- [x] Schema (`0011_campaign_scoping.sql`): `campaigns.scope_conversation`/
      `content_plan`, `variants.target_platforms`. Old campaign-level
      variant_count/media_type/audio columns kept only as a fallback default.
- [x] `llm.continue_campaign_scoping` (+ new `_auto_tool_call` helper) — one
      call per turn, Claude either asks a follow-up or calls
      `finalize_campaign_plan`. `step2_variants._expand_content_plan` +
      rewritten `ideate_variants` expand the plan into per-variant specs.
      `step3_copywriting` only writes captions for a variant's
      `target_platforms`; Step 4 needed no change since it posts wherever a
      caption exists.
- [x] Backend: `POST /campaigns/{id}/scope/messages`, `POST .../scope/confirm`
      (replaces the old `POST .../ideate`). Frontend: `/intake` no longer
      shows variant/media-type/audio fields; new `/campaign/[id]/scope` chat
      page with a structured "Plan ready" card (per-group cards, not one
      paragraph — fixed after real UI testing showed the plain-text summary
      alone wasn't useful).
- [x] Real market research: Claude has access to `web_search` (capped
      `max_uses: 3`, confirmed billing-accurate via
      `usage.server_tool_use.web_search_requests`), but only reaches for it
      when the user seems unsure/wants Claude to decide — not automatic, by
      explicit choice. Every plan item always carries a real `concept` (shot/
      scene description), not just a format.
- [x] Background music is mandatory for every video piece (forced server-side,
      not left to the LLM); voiceover is optional and the agent must
      explicitly ask before finalizing any plan with video, never decide
      silently. Both verified live with real API calls.
- [x] Scoping is platform-connection-aware — queries `social_accounts` and
      flags an unconnected platform before finalizing instead of silently
      planning for it. Verified live.
- [x] **Fixed a real regression**: audio was silently never generated for any
      scoped campaign — the gate still checked the old campaign-level
      `include_voiceover`/`include_music` columns, which scoping never sets
      (found via `ffprobe` on an actual "generated" video: zero audio
      streams, no recorded error). Fixed to gate on the variant's own
      `voiceover_script`/`music_prompt` instead.
- [x] End-to-end through the actual UI — confirmed by extensive real usage
      since: the moodboard/reference-image and product-library work below was
      all built and bug-fixed (asset-path fix, moodboard-response fix, brand
      guideline edit fix) by running real campaigns through
      `/intake` → `/scope` → `/prompts` → generate repeatedly.
- [ ] Fresh video generation not yet re-verified after the audio-gating fix
      above — confirm with a real `ffprobe` check that audio actually comes
      through now. (No direct evidence this specific check has been re-run
      since the fix — worth a real generation + `ffprobe` pass to close out.)
- [ ] Audio partial-failure handling (one of voiceover/music fails, the other
      still ships) is implemented but not yet seen in a real run where both
      calls succeed together.
- [ ] **Platform targeting is locked in at scoping time** — no way to widen an
      already-generated variant to more platforms later without re-scoping.
      Mitigation for now: name every platform you might want upfront. Real
      fix would need a "generate caption for this additional platform" action.
- [ ] **Mid-campaign adaptive check-in** (not built) — scoping is one-shot,
      before anything is generated; no way to revisit a plan once pieces are
      live and earning real engagement. Bigger than the scoping work above:
      needs either multi-wave campaigns or agent-initiated follow-up
      campaigns, and brushes against the "no scheduled/recurring tasks"
      boundary already drawn. Own design pass if pursued.
- [ ] **Real past-performance data feeding into scoping** (not built) — plans
      today come from brand guidelines + judgment (+ research), never from
      this brand's own real engagement data, even though `post_metrics` +
      `engagement_score` + the posting-time model already exist. Would need a
      read-only aggregation tool, same pattern as `web_search`, with the same
      "not enough data yet" gate the posting-time model uses. Natural
      prerequisite for the check-in idea above to be genuinely smart.
- [ ] **Upfront credit/cost estimate before generation** — show an estimated $
      cost on the prompt-review screen before "Generate selected." Future
      iteration, not current scope.

## Brand Library

Redesigned brand management to eliminate duplicate brand creation across campaigns.
Brands are now reusable presets stored in a library, separate from campaign creation.

- [x] Database migration (`0012_brand_library.sql`) — added `description` and
      `brand_voice_id` columns to `brands` table, added index on `user_id` + `created_at`
- [x] Backend API routes — `GET /brands/{id}` endpoint, updated `POST /brands` to
      accept description parameter
- [x] Brand library UI (`/brands` page) — grid view of all user's brands with
      name, description preview, primary color badge, and "Create campaign" links
- [x] Brand creation form (`/brands/new` page) — standalone form for creating
      reusable brand presets (name, description, guidelines text + files)
- [x] Updated campaign intake flow (`/intake` page) — replaced old flow with
      brand selection/creation toggle. Supports:
      - Selecting from existing brands via dropdown
      - Creating new brands inline without leaving campaign flow
      - Pre-selection via `?brand_id=` query parameter
      - Auto-detection if user has no brands (forces create mode)
- [x] **Brand editing** — `/brands/[id]/edit` page updates name, description,
      and guidelines after creation.
- [x] **Brand archiving/deletion** — soft-delete via `archived` column
      (`0014_brand_archiving.sql`); `DELETE /brands/{id}` archives rather than
      hard-deletes, so existing campaigns keep their reference.
- [ ] **Brand analytics** — show campaign count and aggregated performance metrics
      per brand in the library view
- [x] **Product library** — `0017_product_library.sql` + full CRUD in
      `routers/products.py`; `/products` (library grid) and `/products/new`
      pages. Later hardened (`Fix - product library asset path`) and extended
      to let a product carry its own brand voice
      (`de55ca1 Feat - Allow product library + brand voice`).
- [x] **Moodboard upload during scoping conversation** — shipped as "Reference
      image intake": `0015_campaign_moodboard.sql` (campaign-level) extended by
      `0020_variant_reference_asset.sql` (per-variant reference image), with
      `llm.py`/`step2_variants.py` using it to guide generation. Iterated live
      (`Fix - optimize moodboard analysis response`).

## Copywriting (Step 3)

- [x] **Improve caption/hashtag quality across platforms** — enhanced with
      comprehensive platform-specific best practices based on real social media
      performance patterns. Single optimized LLM call now includes:
      - Instagram: Hook-first structure, optimal caption length (125-150 char preview),
        emoji usage (2-4), strategic hashtag mix (8-15: popular/niche/branded), clear CTAs
      - TikTok: Ultra-short captions (max 100 char), question/curiosity hooks,
        conversational tone, 3-5 hashtags (trending + niche), anti-corporate speak
      - Facebook: Longer-form allowed (3-5 sentences), community-building tone,
        minimal hashtags (1-3), story-driven engagement
      - Core principles: front-load value, write for humans first/algorithms second,
        avoid generic filler, every word earns its place
- [ ] **Generate multiple caption variants per platform** — future iteration to
      give users choice between 2-3 options per platform (would require schema
      change or UI update to handle variant selection)
- [ ] **Feed real engagement data into copywriting** — once enough post_metrics
      accumulate, analyze what caption patterns actually perform well for this
      brand/category and feed that back into the prompt (requires aggregation
      tool similar to posting-time model)

## Housekeeping

- [ ] `next` (14.2.35) has known advisories per `npm audit` — none introduced
      by this repo, all in `next` itself. Deliberate upgrade pass needed, not
      a drive-by bump.
- [ ] **Production Supabase project** — currently free tier (auto-pauses after
      7 days idle, weaker backups). Before real launch: separate paid project,
      all migrations fresh, deployed backend pointed there — keep real
      customer data away from this project's accumulated test brands/campaigns.
