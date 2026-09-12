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

## Housekeeping

- [ ] `next` (14.2.35) has several known advisories per `npm audit` in `apps/web`
      (DoS via Image Optimizer, HTTP request smuggling in rewrites, Server
      Components DoS) — none introduced by anything in this repo, all in `next`
      itself. Worth a deliberate upgrade pass + re-test, not a drive-by bump.
