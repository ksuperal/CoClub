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
