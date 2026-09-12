"""Best-posting-time recommendation — gated behind a minimum amount of real data,
not a trained model. With few real posts there's nothing for a model to learn; this
is honest aggregation (bucket real posts by the hour they went out, average their
engagement score per bucket) that does nothing until there's enough history to say
something meaningful. Feeds off the same `posts`/`post_metrics` data the metrics
graph (`step5_feedback.refresh_metrics`) collects — every refresh call quietly builds
toward the day this has enough to recommend anything.

Known simplifications, not fixed here:
- Hour-of-day only, not hour+day-of-week — 24 buckets are already thin on sparse
  data; 168 (24*7) would starve every bucket for far longer.
- Buckets in UTC, not the brand's local time — no account/brand timezone is stored
  anywhere yet.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

from supabase import Client

from .scoring import engagement_score

MIN_POSTS_FOR_RECOMMENDATION = 10
# (min_data_points, confidence) — first threshold met (in order) wins; below all of
# these (but >= MIN_POSTS_FOR_RECOMMENDATION) falls through to "low". Arbitrary
# starting cutoffs, easy to retune once real usage shows what's sensible.
_CONFIDENCE_TIERS = [(100, "high"), (30, "medium")]


def _confidence_for(data_points: int) -> str:
    for threshold, label in _CONFIDENCE_TIERS:
        if data_points >= threshold:
            return label
    return "low"


def recommend_posting_hour(client: Client, *, user_id: str, platform: str) -> dict[str, Any]:
    campaign_ids = [c["id"] for c in client.table("campaigns").select("id").eq("user_id", user_id).execute().data]
    if not campaign_ids:
        return {"platform": platform, "recommended_hour_utc": None, "data_points": 0, "confidence": "insufficient_data"}

    variant_ids = [
        v["id"] for v in client.table("variants").select("id").in_("campaign_id", campaign_ids).execute().data
    ]
    if not variant_ids:
        return {"platform": platform, "recommended_hour_utc": None, "data_points": 0, "confidence": "insufficient_data"}

    posts = (
        client.table("posts")
        .select("id, posted_at")
        .in_("variant_id", variant_ids)
        .eq("platform", platform)
        .eq("status", "posted")
        .not_.is_("posted_at", "null")
        .execute()
        .data
    )
    if not posts:
        return {"platform": platform, "recommended_hour_utc": None, "data_points": 0, "confidence": "insufficient_data"}

    post_ids = [p["id"] for p in posts]
    metrics_rows = client.table("post_metrics").select("*").in_("post_id", post_ids).execute().data
    # A post can have multiple metrics snapshots over time (refresh_metrics accumulates
    # history) — use only the most recent snapshot per post so a frequently-refreshed
    # post isn't over-weighted against one only fetched once.
    latest_metrics_by_post_id: dict[str, dict[str, Any]] = {}
    for m in metrics_rows:
        existing = latest_metrics_by_post_id.get(m["post_id"])
        if not existing or m["fetched_at"] > existing["fetched_at"]:
            latest_metrics_by_post_id[m["post_id"]] = m

    hour_scores: dict[int, list[int]] = defaultdict(list)
    for post in posts:
        metrics = latest_metrics_by_post_id.get(post["id"])
        if not metrics:
            continue
        hour = datetime.fromisoformat(post["posted_at"].replace("Z", "+00:00")).hour
        hour_scores[hour].append(engagement_score(metrics))

    data_points = sum(len(scores) for scores in hour_scores.values())
    if data_points < MIN_POSTS_FOR_RECOMMENDATION:
        return {
            "platform": platform,
            "recommended_hour_utc": None,
            "data_points": data_points,
            "confidence": "insufficient_data",
        }

    best_hour = max(hour_scores, key=lambda h: sum(hour_scores[h]) / len(hour_scores[h]))
    return {
        "platform": platform,
        "recommended_hour_utc": best_hour,
        "data_points": data_points,
        "confidence": _confidence_for(data_points),
    }
