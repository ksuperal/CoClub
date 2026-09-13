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

- [ ] **Run migration `0006_video_generation.sql`** in the Supabase SQL editor —
      nothing video-related works until this is applied (adds `variants.media_type`
      /`motion_prompt`/`video_url`/`generation_status`/`video_gen_job_id`/
      `video_gen_error`, `campaigns.media_type`, and the `awaiting_prompt_review`
      campaign status).
- [ ] **`pip install -r requirements.txt`** again in `apps/api` — no new packages
      were needed for Luma either (reuses `httpx`), but confirm the venv is current.
- [ ] **Real Luma API key** (`LUMA_API_KEY`, from platform.lumalabs.ai, prefixed
      `luma-api-`) — without it, video generation fails cleanly per variant
      (`generation_status = 'failed'`) rather than crashing, but nothing actually
      generates. Unresolved prerequisite, not a code task. (Switched from Higgsfield
      to Luma's Ray model — a background pricing comparison flagged Luma as
      cheaper and better at preserving the source product's look; swapping vendors
      again later only means touching `services/luma.py`'s two functions, nothing
      else in the pipeline depends on which vendor is behind them.)
- [ ] **Inline base64 image upload has an unconfirmed size ceiling** —
      `services/luma.py` sends the starting image as inline base64
      (`video.start_frame.data`) rather than uploading it to a hosted URL first.
      Luma's docs call this "only for small media files" without a hard number; a
      typical single ad-creative PNG should be fine, but this hasn't been tested
      against Luma's actual limit. If it ever fails on a real (larger) image, the
      fix is switching to Luma's Files API (`POST /v1/files`) and referencing the
      resulting `file_id` instead.
- [ ] **Facebook video posting** (`_post_video_to_facebook` in `services/social.py`)
      uses the simple `file_url` param on `/{page_id}/videos` — not yet verified
      against a live Page. Meta's documented path for larger files is a
      resumable/chunked upload session; `file_url` may need to fall back to that
      above some size. Test with a real video before relying on it.
- [ ] **TikTok video posting** — same domain-verification prerequisite as the
      existing photo path should carry over (video URLs come from the same
      verified storage domain), but hasn't been tested end-to-end yet.
- [ ] Video variants currently move the campaign straight to `awaiting_approval`
      once `generate-media` returns, even though the video itself may still be
      `generating` in the background (polled separately) — the variant review
      screen shows a "Generating…" placeholder and disables its approve checkbox
      until `generation_status = 'generated'`, but there's no notification when it
      finishes; the user has to revisit the page.
- [ ] **Split image vs. video into two separate intake screens, switched by a
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

## Agent interface (future — not MVP)

- [ ] **Migrate toward an agent-driven interface, alongside (not replacing) the
      fixed wizard** — triggered by evaluating Higgsfield Supercomputer. Full
      phased plan written up in `docs/agent-migration-plan.md` (schema, tool
      surface wrapping existing pipeline functions, human-in-the-loop approval
      gates on the two real-spend actions, backend/frontend). Explicitly deferred:
      scheduled/recurring agent tasks, new non-social connectors, OpenRouter
      multi-model routing — none needed for MVP.
- [x] **Audio (voiceover + background music) for video variants** — implemented.
      Opt-in per campaign via **two independent toggles** ("Add voiceover
      narration" / "Add background music" at intake, video campaigns only — not
      one combined checkbox). Voiceover via OpenAI `gpt-4o-mini-tts` (reuses
      `OPENAI_API_KEY`, no new account — `services/openai_tts.py`); music via
      ElevenLabs Music API (`ELEVENLABS_API_KEY` — `services/elevenlabs_music.py`);
      mixed + muxed onto the video via `ffmpeg` (`services/audio_mix.py`, handles
      voiceover-only / music-only / both). Claude writes a per-variant script/
      delivery-direction/music-style set during ideation (`llm.write_audio_script`)
      regardless of which toggle(s) are on (cheap, one call) — only the relevant
      field(s) are shown on the prompt-review screen and actually generated.
      Each brand gets one consistent voice, chosen once at intake from its
      guideline's tone (`llm.choose_brand_voice`).
      - [x] Migration `0007_audio.sql` applied.
      - [x] `ffmpeg` installed and confirmed on PATH.
      - [x] `LUMA_API_KEY` and `ELEVENLABS_API_KEY` (Music Generation scope only)
            both added.
      - [ ] **Run migration `0008_split_audio_toggles.sql`** — adds
            `campaigns.include_voiceover` / `include_music`, drops the old
            combined `include_audio` column. Not yet applied.
      - [ ] Not yet tested against a live Luma video end-to-end with the split
            toggles — the ffmpeg commands themselves (both the `amix`-ducked
            two-track case and the single-track voiceover-only/music-only case)
            are standard and well-documented, but unverified for real in this
            environment.
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
