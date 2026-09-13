# TODO

## Feedback / analytics (Step 5)

- [x] Analytics page shows a real graph (`MetricsChart.tsx`, `/campaign/[id]`) —
      decoupled from the LLM report via `POST .../metrics/refresh` +
      `GET .../metrics/history` (`step5_feedback.refresh_metrics`).
- [x] Feedback report renders as actual markdown (`react-markdown`), not raw `**`.
- [x] Best-posting-time recommendation (`services/posting_time.py`, real ML —
      RidgeCV over a cyclical hour-of-day encoding) is wired into the variant
      review screen, gated behind 10+ real posts *with* metrics data on a
      platform — invisible until there's enough to say something real.
- [ ] **Ads/boost integration** — a separate API from what's built (Graph API is
      organic-only): Meta's **Marketing API**, needing `ads_read` (read-only spend/
      reach/CPM, lower review burden) or `ads_management` (app actually spends the
      customer's money — real financial-transaction liability, its own Ad Account
      connection per customer, harder review). Recommended staged approach:
      1. Now/next: **deep-link** the Recommendation section's suggested variant into
         Meta's own native "Boost Post" flow — Meta handles all spend/payment/
         confirmation UI, CoClub never touches money.
      2. Later, only if wanted: add `ads_read` to cite real cost/reach numbers in
         the recommendation instead of staying directional.
      3. `ads_management` (CoClub programmatically spending on the customer's
         behalf) — probably never; the liability/UX cost is high for what it adds
         over option 1.

## Video generation + posting

- [x] **Run migration `0006_video_generation.sql`** in the Supabase SQL editor —
      nothing video-related works until this is applied (adds `variants.media_type`
      /`motion_prompt`/`video_url`/`generation_status`/`video_gen_job_id`/
      `video_gen_error`, `campaigns.media_type`, and the `awaiting_prompt_review`
      campaign status).
- [x] **`pip install -r requirements.txt`** again in `apps/api` — no new packages
      were needed for Luma either (reuses `httpx`), but confirm the venv is current.
- [x] **Real Luma API key** (`LUMA_API_KEY`, from platform.lumalabs.ai, prefixed
      `luma-api-`) — without it, video generation fails cleanly per variant
      (`generation_status = 'failed'`) rather than crashing, but nothing actually
      generates. Unresolved prerequisite, not a code task. (Switched from Higgsfield
      to Luma's Ray model — a background pricing comparison flagged Luma as
      cheaper and better at preserving the source product's look; swapping vendors
      again later only means touching `services/luma.py`'s two functions, nothing
      else in the pipeline depends on which vendor is behind them.)
- [x] **Inline base64 image upload has an unconfirmed size ceiling** —
      `services/luma.py` sends the starting image as inline base64
      (`video.start_frame.data`) rather than uploading it to a hosted URL first.
      Luma's docs call this "only for small media files" without a hard number; a
      typical single ad-creative PNG should be fine, but this hasn't been tested
      against Luma's actual limit. If it ever fails on a real (larger) image, the
      fix is switching to Luma's Files API (`POST /v1/files`) and referencing the
      resulting `file_id` instead.
- [x] **Facebook video posting** (`_post_video_to_facebook` in `services/social.py`)
      uses the simple `file_url` param on `/{page_id}/videos` — not yet verified
      against a live Page. Meta's documented path for larger files is a
      resumable/chunked upload session; `file_url` may need to fall back to that
      above some size. Test with a real video before relying on it.
- [ ] **TikTok video posting** — same domain-verification prerequisite as the
      existing photo path should carry over (video URLs come from the same
      verified storage domain), but hasn't been tested end-to-end yet.
- [x] Video variants currently move the campaign straight to `awaiting_approval`
      once `generate-media` returns, even though the video itself may still be
      `generating` in the background (polled separately) — the variant review
      screen shows a "Generating…" placeholder and disables its approve checkbox
      until `generation_status = 'generated'`, but there's no notification when it
      finishes; the user has to revisit the page.
- [x] **Split image vs. video into two separate intake screens, switched by a
      toggle button** — instead of today's single `/intake` form with an embedded
      "Generate as: Image / Video" radio pair (`apps/web/app/intake/page.tsx`)
      that shows/hides fields inline. Two distinct screens (e.g. a top-level
      toggle that swaps which form renders, or two routes like `/intake/image`
      and `/intake/video`) so each medium's intake can diverge on its own terms
      as video-specific options grow (resolution/duration once exposed, motion
      style presets, etc.) without both crowding one form. Needs a design
      decision on whether the toggle lives above the form (single route,
      client-side swap) or as separate routes — affects how `media_type` state
      and the shared fields (brand/product/campaign brief) are threaded through.

## Campaign scoping (conversational, embedded in the wizard)

- [x] **Standalone chat agent built, tried, and removed.** `docs/agent-migration-plan.md`
      (Phases 0-4 — 17-tool agent, `/agent` chat page) was fully implemented, then
      deliberately deleted: it just re-asked the wizard's own form questions via
      chat, no real advantage over the form. Migration `0009_agent.sql` reversed
      by `0010_drop_agent_tables.sql`. Superseded by the design below — kept the
      `anthropic` SDK bump (0.42.0 → 1.5.0) since it's a real, verified-safe
      improvement even though Tool Runner is no longer used by anything.
- [x] **What replaced it**: intake no longer asks the user to pick
      `variant_count`/`media_type`/audio toggles from a form. Campaign creation
      (brand + product + brief, unchanged) is followed by a short, *purpose-built*
      conversational step — `/campaign/[id]/scope` — that asks "how big a campaign
      do you want?" and lets the user answer in their own words ("IG 9 posts,
      TikTok 2 short videos with voiceover"). Claude either asks a focused
      follow-up or finalizes a concrete **content plan**: a list of groups, each
      with `media_type`, `target_platforms`, `count`, and audio toggles — shown
      to the user as a plain-language summary before anything is written.
      Confirming hands off to the *exact same* `ideate_variants` → prompt review
      → `generate_variant_media` → caption editing → approve & post → feedback
      pipeline that already existed, completely unchanged from that point on.
      - [x] Schema (`0011_campaign_scoping.sql`): `campaigns.scope_conversation`
            (transcript, for resuming), `campaigns.content_plan` (the finalized
            plan), `variants.target_platforms` (empty = no restriction, the old
            behavior). The old `variant_count`/`media_type`/audio-toggle columns
            stay as a fallback default for any campaign that somehow has no plan
            — not dropped, just no longer the primary path.
      - [x] `llm.continue_campaign_scoping` — one call per turn, `tool_choice:
            "auto"` (not forced) so Claude can either ask a question in plain
            text or call `finalize_campaign_plan`. New `_auto_tool_call` helper
            in `llm.py` alongside the existing `_forced_tool_call`.
      - [x] `step2_variants._expand_content_plan` + rewritten `ideate_variants` —
            expands the plan into per-variant specs (heterogeneous media_type/
            platforms/audio within one campaign, not the old one-setting-for-all).
            One shared `ideate_message_angles` call across the whole plan (total
            count), so angles stay distinct campaign-wide rather than repeating
            per group.
      - [x] `step3_copywriting.run_copywriting` — only writes captions for a
            variant's `target_platforms` when set (falls back to all 3 when
            empty). `step4_approve_post.post_campaign` needed **no change** —
            it already posts wherever a caption exists, so platform targeting
            "just works" once Step 3 respects it.
      - [x] Backend: `POST /campaigns/{id}/scope/messages` (one turn),
            `POST /campaigns/{id}/scope/confirm` (locks the plan, calls
            `ideate_variants`). Replaces the old `POST .../ideate`.
      - [x] Frontend: `/campaign/[id]/intake` no longer shows variant count/media
            type/audio fields; `/campaign/[id]/scope` (new) is a small chat UI
            with a canned opening question and a "Plan ready" confirmation card;
            `/campaign/[id]/prompts`'s per-variant audio fields are now driven
            per-variant (`voiceover_script`/`music_prompt` non-null) instead of
            one campaign-wide flag, since a plan can mix settings within one
            campaign. All three review pages show a target-platform badge.
      - [ ] **Not yet tested end-to-end through the actual UI** — migrations
            `0009`/`0010`/`0011` need to be applied in order (0009 was already
            applied before the pivot; 0010 reverses it, 0011 adds the real
            schema). The backend logic itself (`llm.continue_campaign_scoping`)
            has been smoke-tested directly with real API calls — see below.
- [x] **Market research + real creative concepts in scoping.** `continue_campaign_scoping`
      now does two more things than "decide format/count": every plan item
      always carries a `concept` field (a real shot/scene description, e.g.
      "product reveal on clean studio background" — not just a format), and
      Claude has access to Anthropic's server-side `web_search` tool
      (`web_search_20260209`, `max_uses: 3`). Per the user's explicit choice,
      search is **not** automatic — the system prompt only reaches for it when
      the user seems unsure or explicitly asks Claude to decide ("I don't know",
      "come up with something"); concrete requests ("IG 9 posts") get concepts
      filled in from brand context and marketing judgment, no search, no extra
      cost. `message_angle` (the strategic hook) and `concept` (the literal
      shot) now both flow into `write_image_prompt`/`ideate_motion_prompt`/
      `write_audio_script` together.
      - [x] Verified live, twice, with real API calls (not just read the code):
            a concrete request ("IG 9 posts, TikTok 2 videos") correctly
            finalized immediately with no search, auto-splitting the 9 posts
            into 3 distinct concept groups on its own initiative. A vague
            request ("I don't know, come up with something") correctly
            triggered real web searches (confirmed via
            `response.usage.server_tool_use.web_search_requests`, the
            authoritative billed count — 3, exactly matching `max_uses`) and
            came back with a genuinely researched, multi-platform, multi-concept
            plan citing what informed it.
      - [x] Confirmed `max_uses` is a real, billing-accurate cap — an earlier
            look at raw response content blocks appeared to show far more than
            3 searches (Claude's dynamic-filtering code sometimes writes several
            *candidate* query strings inside one code_execution block before
            picking which to actually run), which looked alarming until checked
            against `usage.server_tool_use.web_search_requests` directly — that
            field, not a content-block count, is the number that's actually
            billed, and it matched `max_uses` exactly in both tests.
- [x] **Fixed: audio was silently never generated for any scoped (content_plan)
      campaign.** Real regression from the scoping pivot, found via real UI
      testing (downloaded and `ffprobe`'d an actual "generated" video — zero
      audio streams, despite `audio_gen_error: None`). Root cause: the audio-
      generation gate in `poll_video_generation_job`/`_generate_and_mux_audio`
      still checked the old campaign-level `include_voiceover`/`include_music`
      columns — which the scoping flow never sets (that decision is per-variant
      now, in `content_plan`), so the gate was always false and the whole audio
      branch was skipped, not attempted-and-failed. Fixed to gate on the
      variant's own `voiceover_script`/`music_prompt` being non-null instead —
      the actual per-variant signal, correct regardless of which flow created
      the variant. Not yet re-verified with a fresh end-to-end video generation
      (only diagnosed and fixed) — worth one more real test.
- [x] **Background music is now mandatory for every video piece; voiceover is
      genuinely optional and the scoping agent must ask about it.** Explicit
      user decision: music is never a judgment call — `continue_campaign_scoping`
      no longer even lets Claude set `include_music` (removed from the tool
      schema entirely); the code forces it `True` for every video item after
      the fact, a structural guarantee rather than a prompt instruction, same
      pattern as other hard guarantees in this codebase. Voiceover stays
      Claude's call, but the system prompt now requires it to explicitly ask
      the user before finalizing any plan with video — never silently decide
      either way. Verified live with real API calls: a video request with no
      voiceover mention correctly returned a question instead of finalizing;
      after the user answered "no voiceover, just music," the finalized plan
      had `include_voiceover: false` (matching the answer) and
      `include_music: true` (forced) on the video item.
- [ ] **Platform targeting is locked in at scoping time, with no way to widen
      it later.** If a plan targets "Instagram only," there's currently no way
      to also post that same variant to Facebook/TikTok afterward without
      re-scoping the whole campaign — `target_platforms` is set once during
      ideation and Step 3 only ever writes captions for those platforms.
      Near-term mitigation: just name every platform you might want during the
      scoping conversation ("IG and Facebook"), even if unsure — costs nothing
      extra. Real fix (not built): let a user add a platform to an already-
      generated variant, which needs a new "generate caption for this
      additional platform" action, not just an editable field.
- [x] **Scoping is now platform-connection aware.** The scoping call didn't
      know which social accounts were actually connected — it could propose
      "TikTok 2 videos" for a user with no TikTok linked, which would just sit
      as `pending_credentials` forever. Fixed: `routers/campaigns.py`'s
      `/scope/messages` now queries `social_accounts` (status='connected') and
      passes the list into `continue_campaign_scoping`; the prompt requires
      flagging an unconnected platform before finalizing rather than silently
      planning for it. Verified live: asking for "TikTok 3 image posts" with
      only Instagram connected correctly came back as a question ("you don't
      have TikTok connected yet... want me to plan for it anyway, or target
      Instagram instead?") rather than finalizing blind.
- [ ] **Not built yet: mid-campaign adaptive check-in.** Scoping is a one-shot
      decision entirely before anything is generated — there's no way for the
      agent to revisit a plan once some pieces are actually live and earning
      real engagement ("your first 3 posts are up, want me to adjust the rest
      based on how they're doing?"). This is a genuinely bigger piece than the
      scoping work above: today, once `generate_variant_media` runs, that's a
      campaign's final batch — there's no concept of adding more variants to
      an *existing* campaign later informed by how the first wave performed.
      Two shapes it could take: (a) extend campaigns to support multiple waves
      over time, or (b) have the agent proactively suggest spinning up a *new*
      campaign at a natural checkpoint, informed by the last one's real
      results (ties into the performance-data idea below). Either way it
      brushes against the "no scheduled/recurring agent tasks" boundary
      already drawn earlier — a check-in needs either the user manually
      returning, or a scheduled job to prompt them, which is new
      infrastructure, not a prompt change. Deserves its own design pass if
      pursued, not a quick addition.
- [ ] **Not built yet: real past-performance data feeding into scoping.** Every
      plan today comes from brand guidelines + general marketing judgment (+
      research, when triggered) — never from *this brand's own real engagement
      data*, even though the infrastructure already exists (`post_metrics`,
      `services/scoring.py`'s `engagement_score`, the posting-time ML model).
      Would need: a new read-only aggregation (past variants' message_angle/
      concept/media_type/target_platforms, joined to posts → post_metrics,
      summarized — "video averages 2.3x the engagement of image for this
      brand") exposed as a tool the scoping call can reach for, same pattern
      as `web_search`. Real caveat: cold start — only useful from a brand's
      2nd+ campaign, and needs the same "don't trust it until there's enough
      data" gate the posting-time model already uses
      (`MIN_POSTS_FOR_RECOMMENDATION`) so a handful of noisy posts doesn't
      masquerade as a real trend.
- [x] **Audio (voiceover + background music) for video variants** — implemented
      and fully configured end-to-end. Opt-in per campaign via **two independent
      toggles** ("Add voiceover narration" / "Add background music" at intake,
      video campaigns only). **Both voiceover and music now run on ElevenLabs**
      (`ELEVENLABS_API_KEY`, one key for both) — voiceover switched from OpenAI's
      `gpt-4o-mini-tts` to ElevenLabs' `eleven_v3` (`services/elevenlabs_tts.py`)
      after real testing showed OpenAI's output reading as flat/monotone;
      `eleven_v3` controls delivery via inline audio tags Claude writes directly
      into the script (`[excited]`, `[sighs]`, etc.) plus a deliberately-lowered
      `stability` setting, not a separate freeform instructions string. Music
      via ElevenLabs Music API (`services/elevenlabs_music.py`); mixed + muxed
      onto the video via `ffmpeg` (`services/audio_mix.py`, handles voiceover-
      only / music-only / both). Claude writes a per-variant script/delivery-
      summary/music-style set during ideation (`llm.write_audio_script`) —
      explicitly instructed not to narrate the message angle's concept as
      literal words (real bug hit in testing: angle "chaos to calm" → script
      "Chaos in. Calm out." — fixed by requiring real ad copy, with the arc
      expressed through audio tags instead). Each brand gets one consistent
      voice, chosen once at intake from a live-fetched ElevenLabs voice list
      matched to the brand's tone (`llm.choose_brand_voice`).
      - [x] Migrations `0007_audio.sql` and `0008_split_audio_toggles.sql` applied.
      - [x] `ffmpeg` installed and confirmed on PATH.
      - [x] `LUMA_API_KEY` added.
      - [x] `ELEVENLABS_API_KEY` added with all required scopes confirmed live:
            Music Generation (Access), Text to Speech (Access), Voices (Read).
      - [ ] Partial-failure handling (one of voiceover/music fails, the other
            ships) is implemented and code-reviewed but the actual ElevenLabs
            calls haven't both succeeded together in one real end-to-end test
            yet — worth one more full run to confirm.
- [ ] **Upfront credit/cost estimate before generation** — show an estimated $ cost
      on the prompt-review screen (`/campaign/[id]/prompts`) before "Generate
      selected," similar to how Supercomputer shows credit cost before a
      generation runs. Future MVP iteration, not current scope.

## Copywriting (Step 3)

- [ ] **Improve caption/hashtag quality across all platforms** — currently one
      LLM call (`llm.write_captions`, invoked from `pipeline/step3_copywriting.py`)
      generates all platforms' captions together off a single system prompt with
      just a sentence of style guidance per platform (Instagram: "medium length,
      SEO-style"; TikTok: "short, punchy, high-velocity hashtags"; Facebook: "can
      be slightly longer"). No dedicated research into what actually performs
      well per platform yet. Candidate directions, not yet decided between:
      1. Split into one LLM call per platform with a much more detailed,
         platform-specific system prompt (current character-limit/format norms,
         hook-writing patterns, hashtag-count conventions) — more tokens/cost per
         campaign, likely better per-platform quality.
      2. Feed real engagement data back in once it accumulates (ties into the
         Step 5 metrics pipeline already built) — e.g. surface which past
         captions' styles correlated with higher `engagement_score` as few-shot
         context for future generations, rather than a static prompt forever.
      3. Generate multiple caption variants per platform and let the user pick,
         instead of one committed caption per platform today.

## Housekeeping

- [ ] `next` (14.2.35) has several known advisories per `npm audit` in `apps/web`
      (DoS via Image Optimizer, HTTP request smuggling in rewrites, Server
      Components DoS) — none introduced by anything in this repo, all in `next`
      itself. Worth a deliberate upgrade pass + re-test, not a drive-by bump.
- [ ] **Production Supabase project** — currently on the free tier, which
      auto-pauses after 7 days of no API activity (fine for solo dev, not
      acceptable once real customers depend on it) and has weaker backup
      guarantees. Before real launch: spin up a **separate, paid** Supabase
      project for production (don't just upgrade this one), run all 5 migrations
      fresh against it, and point the deployed backend's `.env` there — keeps
      real customer data from ever mixing with this project's accumulated test
      brands/campaigns (the duplicate "Zucgoo"/"Slack" test entries, etc.).
