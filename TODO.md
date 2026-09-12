# TODO

## Feedback / analytics (Step 5)

- [ ] Analytics page (`/campaign/[id]`'s feedback report, or a dedicated analytics view)
      should show data as **graphs**, not just the LLM-narrated text summary it renders
      today (see `campaign_reports.summary_text`, `apps/api/app/pipeline/step5_feedback.py`).
- [ ] Consider connecting to **Meta Ads Manager** (and TikTok's equivalent) so the
      feedback step can surface whether a post is a good candidate to **boost** —
      i.e. pull ad-eligible performance signals, not just organic `post_metrics`
      (likes/comments/shares/views already collected via `social.fetch_metrics`).
