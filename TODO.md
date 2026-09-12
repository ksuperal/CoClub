# TODO

## Feedback / analytics (Step 5)

- [x] Analytics page shows a real graph (`MetricsChart.tsx`, `/campaign/[id]`) —
      decoupled from the LLM report via `POST .../metrics/refresh` +
      `GET .../metrics/history` (`step5_feedback.refresh_metrics`).
- [x] Feedback report renders as actual markdown (`react-markdown`), not raw `**`.
- [ ] Best-posting-time recommendation (`services/posting_time.py`,
      `GET /social/posting-time-recommendation/{platform}`) is built but gated
      behind 10+ real posts on a platform — not surfaced in the UI yet. Wire it in
      once real usage data makes it worth showing.
- [ ] Consider connecting to **Meta Ads Manager** (and TikTok's equivalent) so the
      feedback step can surface whether a post is a good candidate to **boost** —
      i.e. pull ad-eligible performance signals, not just organic `post_metrics`
      (likes/comments/shares/views already collected via `social.fetch_metrics`).

## Housekeeping

- [ ] `next` (14.2.35) has several known advisories per `npm audit` in `apps/web`
      (DoS via Image Optimizer, HTTP request smuggling in rewrites, Server
      Components DoS) — none introduced by anything in this repo, all in `next`
      itself. Worth a deliberate upgrade pass + re-test, not a drive-by bump.
