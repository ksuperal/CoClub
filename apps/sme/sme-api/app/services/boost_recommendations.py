"""AI-powered boost recommendations after 72-hour metrics collection.

This module analyzes post performance and suggests which posts should be boosted,
with recommended budgets and targeting strategies.
"""

import logging
from typing import Any

from supabase import Client

logger = logging.getLogger(__name__)


def should_recommend_boost(
    *,
    metrics: dict[str, Any],
    expected_thresholds: dict[str, Any],
    primary_metric: str,
    campaign_type: str,
) -> dict[str, Any] | None:
    """Determine if a post should be recommended for boosting.

    Args:
        metrics: Actual post metrics after 72 hours
        expected_thresholds: Expected performance levels from campaign creation
        primary_metric: The metric to optimize for (saves, reach, link_clicks, etc.)
        campaign_type: Type of campaign (educational, promotional, etc.)

    Returns:
        Boost recommendation dict if post qualifies, None otherwise
        {
            "should_boost": True,
            "reason": "Educational post exceeded expected saves by 180%",
            "confidence": "high",
            "suggested_budget_daily": 15.00,
            "suggested_duration_days": 7,
            "expected_additional_reach": 25000,
            "objective": "OUTCOME_ENGAGEMENT"
        }
    """
    if not expected_thresholds or primary_metric not in metrics:
        return None

    actual_value = metrics.get(primary_metric, 0)
    excellent_threshold = expected_thresholds.get("excellent", {}).get(primary_metric, 0)
    good_threshold = expected_thresholds.get("good", {}).get(primary_metric, 0)

    # Only recommend boost if post exceeded "good" threshold
    if actual_value < good_threshold:
        return None

    # Calculate performance multiplier
    if excellent_threshold > 0:
        performance_multiplier = actual_value / excellent_threshold
    elif good_threshold > 0:
        performance_multiplier = actual_value / good_threshold
    else:
        return None

    # Only boost if significantly outperforming (1.5x+ of good threshold)
    if performance_multiplier < 1.5:
        return None

    # Determine confidence level
    if performance_multiplier >= 2.0:
        confidence = "high"
    elif performance_multiplier >= 1.5:
        confidence = "medium"
    else:
        confidence = "low"

    # Calculate performance percentage
    performance_pct = int((performance_multiplier - 1) * 100)

    # Determine boost reason
    reason = f"{campaign_type.replace('_', ' ').title()} post exceeded expected {primary_metric} by {performance_pct}% ({actual_value:,} vs {excellent_threshold:,} expected)"

    # Determine objective based on campaign type
    objective_map = {
        "educational": "OUTCOME_ENGAGEMENT",
        "promotional": "OUTCOME_TRAFFIC",
        "brand_awareness": "OUTCOME_AWARENESS",
        "product_launch": "OUTCOME_AWARENESS",
        "event_announcement": "OUTCOME_AWARENESS",
    }
    objective = objective_map.get(campaign_type, "OUTCOME_ENGAGEMENT")

    # Calculate suggested budget based on performance
    # Base budget: $10/day
    # Add $2 for each 50% over threshold
    base_budget = 10.0
    bonus_budget = min((performance_multiplier - 1) * 4, 20.0)  # Cap at +$20
    suggested_budget = round(base_budget + bonus_budget, 2)

    # Suggest duration based on performance
    # High performers: 7 days
    # Medium performers: 5 days
    suggested_duration = 7 if confidence == "high" else 5

    # Estimate additional reach based on budget and platform averages
    # Rough estimate: $1 = 1000-2000 impressions, 30% reach
    estimated_impressions = (suggested_budget * suggested_duration) * 1500
    estimated_reach = int(estimated_impressions * 0.3)

    return {
        "should_boost": True,
        "reason": reason,
        "confidence": confidence,
        "suggested_budget_daily": suggested_budget,
        "suggested_duration_days": suggested_duration,
        "expected_additional_reach": estimated_reach,
        "objective": objective,
        "performance_multiplier": round(performance_multiplier, 2),
        "actual_value": actual_value,
        "expected_value": excellent_threshold,
    }


def generate_boost_recommendations_for_campaign(
    client: Client, *, campaign_id: str
) -> list[dict[str, Any]]:
    """Generate boost recommendations for all posts in a campaign after 72 hours.

    This should be called by the feedback job (step5_feedback.py) after metrics collection completes.

    Args:
        client: Supabase client
        campaign_id: Campaign ID to analyze

    Returns:
        List of boost recommendations, one per qualifying post
        [
            {
                "post_id": "uuid",
                "variant_id": "uuid",
                "platform": "instagram",
                "recommendation": {...}
            }
        ]
    """
    # Get campaign details
    campaign = (
        client.table("campaigns")
        .select("*, primary_metric, expected_thresholds, campaign_type")
        .eq("id", campaign_id)
        .single()
        .execute()
        .data
    )

    if not campaign:
        logger.warning(f"Campaign {campaign_id} not found")
        return []

    primary_metric = campaign.get("primary_metric", "engagement_rate")
    expected_thresholds = campaign.get("expected_thresholds", {})
    campaign_type = campaign.get("campaign_type", "other")

    # Get all posted variants for this campaign
    variants = (
        client.table("variants")
        .select("id")
        .eq("campaign_id", campaign_id)
        .execute()
        .data
    )

    if not variants:
        return []

    variant_ids = [v["id"] for v in variants]

    # Get all posts for these variants
    posts = (
        client.table("posts")
        .select("id, variant_id, platform, status")
        .in_("variant_id", variant_ids)
        .eq("status", "posted")
        .execute()
        .data
    )

    recommendations = []

    for post in posts:
        # Get latest metrics for this post
        latest_metrics = (
            client.table("post_metrics")
            .select("*")
            .eq("post_id", post["id"])
            .order("fetched_at", desc=True)
            .limit(1)
            .execute()
            .data
        )

        if not latest_metrics:
            continue

        metrics = latest_metrics[0]

        # Check if post qualifies for boost recommendation
        recommendation = should_recommend_boost(
            metrics=metrics,
            expected_thresholds=expected_thresholds,
            primary_metric=primary_metric,
            campaign_type=campaign_type,
        )

        if recommendation:
            recommendations.append({
                "post_id": post["id"],
                "variant_id": post["variant_id"],
                "platform": post["platform"],
                "recommendation": recommendation,
            })

    # Sort by performance multiplier (best first)
    recommendations.sort(
        key=lambda x: x["recommendation"]["performance_multiplier"],
        reverse=True
    )

    logger.info(
        f"Generated {len(recommendations)} boost recommendations for campaign {campaign_id}"
    )

    return recommendations


def store_boost_recommendations(
    client: Client,
    *,
    campaign_id: str,
    recommendations: list[dict[str, Any]]
) -> None:
    """Store boost recommendations in content_performance_insights table.

    This allows frontend to display boost suggestions alongside post performance.

    Args:
        client: Supabase client
        campaign_id: Campaign ID
        recommendations: List of recommendations from generate_boost_recommendations_for_campaign
    """
    for rec in recommendations:
        post_id = rec["post_id"]
        recommendation = rec["recommendation"]

        # Check if insight record exists
        existing = (
            client.table("content_performance_insights")
            .select("id")
            .eq("post_id", post_id)
            .execute()
            .data
        )

        boost_suggestion = {
            "should_boost": True,
            "reason": recommendation["reason"],
            "confidence": recommendation["confidence"],
            "suggested_budget": recommendation["suggested_budget_daily"],
            "suggested_duration": recommendation["suggested_duration_days"],
            "expected_reach": recommendation["expected_additional_reach"],
            "objective": recommendation["objective"],
        }

        if existing:
            # Update existing record
            client.table("content_performance_insights").update({
                "ai_analysis": {
                    **(existing[0].get("ai_analysis", {})),
                    "boost_suggestion": boost_suggestion,
                }
            }).eq("id", existing[0]["id"]).execute()
        else:
            # Note: Full insight record should be created by content_analysis.py
            # This just adds the boost suggestion
            logger.warning(
                f"No performance insight found for post {post_id}. "
                "Boost recommendation will be lost."
            )

    logger.info(f"Stored {len(recommendations)} boost recommendations for campaign {campaign_id}")
