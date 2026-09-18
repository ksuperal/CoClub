"""Best-posting-time recommendation — a real (if deliberately simple) ML model:
Ridge regression over a cyclical encoding of hour-of-day, gated behind a minimum
amount of real data. Not a trained deep model — with the data volumes this product
realistically has for a while, a small linear model with cross-validated
regularization is the *correct* amount of ML, not a compromise: a tree ensemble or
anything more expressive would just memorize noise on a few dozen data points.

This is a genuine upgrade over a plain "average per hour bucket," not a cosmetic
one: the model can predict a sensible expected score for an hour with *zero* direct
posts, by interpolating from nearby hours that do have data — plain per-bucket
averaging structurally cannot do that; an empty bucket has nothing to average.

Feeds off the same `posts`/`post_metrics` data the metrics graph
(`step5_feedback.refresh_metrics`) collects — every refresh call quietly builds
toward the day this has enough to recommend anything.

Known simplifications, not fixed here:
- Hour-of-day only, not hour+day-of-week — even a regularized model needs more
  data than this product has today to support a second dimension without just
  fitting noise.
- Buckets/predicts in UTC, not the brand's local time — no account/brand timezone
  is stored anywhere yet.
"""

from datetime import datetime
from typing import Any

import numpy as np
from sklearn.linear_model import RidgeCV
from supabase import Client

from .scoring import engagement_score

MIN_POSTS_FOR_RECOMMENDATION = 10
# (min_data_points, confidence) — first threshold met (in order) wins; below all of
# these (but >= MIN_POSTS_FOR_RECOMMENDATION) falls through to "low". Arbitrary
# starting cutoffs, easy to retune once real usage shows what's sensible. Reflects
# sample size, not the model's fit quality (e.g. cross-validated R²) — with N this
# small, a fit-quality metric would itself be too noisy to be a meaningful signal.
_CONFIDENCE_TIERS = [(100, "high"), (30, "medium")]

# Regularization strengths RidgeCV picks between via built-in cross-validation — a
# wide range so it can land on strong shrinkage (safe default for tiny N, pulls
# predictions toward the overall mean) or lighter shrinkage (once there's enough
# data to trust the hour-to-hour signal more).
_RIDGE_ALPHAS = np.logspace(-2, 3, 20)


def _confidence_for(data_points: int) -> str:
    for threshold, label in _CONFIDENCE_TIERS:
        if data_points >= threshold:
            return label
    return "low"


def _hour_features(hour: int) -> list[float]:
    """Cyclical encoding, not a raw integer or one-hot: hour 23 and hour 0 are
    adjacent in real time, and both a plain integer and a 24-column one-hot lose
    that adjacency (one-hot also costs 24 parameters against a handful of training
    rows — exactly the overfitting risk regularization shouldn't have to fight
    unnecessarily). Two features (sin/cos) capture the 24-hour cycle with far less
    capacity to overfit, and let the model interpolate smoothly between hours."""
    radians = 2 * np.pi * hour / 24
    return [float(np.sin(radians)), float(np.cos(radians))]


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

    X: list[list[float]] = []
    y: list[float] = []
    for post in posts:
        metrics = latest_metrics_by_post_id.get(post["id"])
        if not metrics:
            continue
        hour = datetime.fromisoformat(post["posted_at"].replace("Z", "+00:00")).hour
        X.append(_hour_features(hour))
        y.append(float(engagement_score(metrics)))

    data_points = len(y)
    if data_points < MIN_POSTS_FOR_RECOMMENDATION:
        return {
            "platform": platform,
            "recommended_hour_utc": None,
            "data_points": data_points,
            "confidence": "insufficient_data",
        }

    model = RidgeCV(alphas=_RIDGE_ALPHAS)
    model.fit(np.array(X), np.array(y))

    # Score every hour, including ones with no direct data — this is exactly what a
    # plain per-bucket average can't do; the model interpolates from nearby hours
    # that do have real posts instead of having nothing to say about the rest.
    candidate_hours = list(range(24))
    predicted_scores = model.predict(np.array([_hour_features(h) for h in candidate_hours]))
    best_hour = candidate_hours[int(np.argmax(predicted_scores))]

    return {
        "platform": platform,
        "recommended_hour_utc": best_hour,
        "data_points": data_points,
        "confidence": _confidence_for(data_points),
    }
