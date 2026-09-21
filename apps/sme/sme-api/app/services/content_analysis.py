"""Content performance analysis and recommendation generation."""

import logging
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from . import llm

logger = logging.getLogger(__name__)


def calculate_performance_tier(engagement_score: int, user_avg: float) -> str:
    """Categorize post performance relative to user's average."""
    if engagement_score >= user_avg * 1.5:
        return "excellent"
    elif engagement_score >= user_avg * 1.2:
        return "good"
    elif engagement_score >= user_avg * 0.8:
        return "average"
    elif engagement_score >= user_avg * 0.5:
        return "poor"
    else:
        return "needs_improvement"


def calculate_performance_percentile(engagement_score: int, user_scores: list[int]) -> float:
    """Calculate percentile rank compared to user's other posts."""
    if not user_scores:
        return 50.0  # Default to median if no history

    user_scores_sorted = sorted(user_scores)
    rank = sum(1 for score in user_scores_sorted if score <= engagement_score)
    percentile = (rank / len(user_scores_sorted)) * 100
    return round(percentile, 2)


def get_user_average_performance(
    client: Client, *, user_id: str, platform: str
) -> dict[str, float]:
    """Get user's average performance metrics for a platform."""
    # Get all user's posts on this platform
    query = """
        SELECT
            AVG(pm.likes) as avg_likes,
            AVG(pm.comments) as avg_comments,
            AVG(pm.shares) as avg_shares,
            AVG(pm.views) as avg_views,
            AVG(pm.saves) as avg_saves,
            AVG(pm.reach) as avg_reach
        FROM post_metrics pm
        JOIN posts p ON p.id = pm.post_id
        JOIN variants v ON v.id = p.variant_id
        JOIN campaigns c ON c.id = v.campaign_id
        WHERE c.user_id = :user_id AND p.platform = :platform
    """

    # Since we're using Supabase client, we'll do this differently
    # Get all campaigns for user
    campaigns = client.table("campaigns").select("id").eq("user_id", user_id).execute().data
    campaign_ids = [c["id"] for c in campaigns]

    if not campaign_ids:
        return {
            "avg_engagement_score": 0,
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_shares": 0,
            "avg_views": 0,
        }

    # Get variants for these campaigns
    variants = client.table("variants").select("id").in_("campaign_id", campaign_ids).execute().data
    variant_ids = [v["id"] for v in variants]

    if not variant_ids:
        return {
            "avg_engagement_score": 0,
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_shares": 0,
            "avg_views": 0,
        }

    # Get posts for these variants on this platform
    posts = client.table("posts").select("id").in_("variant_id", variant_ids).eq("platform", platform).execute().data
    post_ids = [p["id"] for p in posts]

    if not post_ids:
        return {
            "avg_engagement_score": 0,
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_shares": 0,
            "avg_views": 0,
        }

    # Get latest metrics for these posts (one per post)
    metrics = []
    for post_id in post_ids:
        latest_metric = (
            client.table("post_metrics")
            .select("*")
            .eq("post_id", post_id)
            .order("fetched_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if latest_metric:
            metrics.append(latest_metric[0])

    if not metrics:
        return {
            "avg_engagement_score": 0,
            "avg_likes": 0,
            "avg_comments": 0,
            "avg_shares": 0,
            "avg_views": 0,
        }

    # Calculate averages
    total_likes = sum(m.get("likes", 0) for m in metrics)
    total_comments = sum(m.get("comments", 0) for m in metrics)
    total_shares = sum(m.get("shares", 0) for m in metrics)
    total_views = sum(m.get("views", 0) for m in metrics)
    count = len(metrics)

    avg_engagement = (total_likes + total_comments + total_shares) / count if count > 0 else 0

    return {
        "avg_engagement_score": round(avg_engagement, 2),
        "avg_likes": round(total_likes / count, 2) if count > 0 else 0,
        "avg_comments": round(total_comments / count, 2) if count > 0 else 0,
        "avg_shares": round(total_shares / count, 2) if count > 0 else 0,
        "avg_views": round(total_views / count, 2) if count > 0 else 0,
    }


def generate_improvement_recommendations(
    *,
    post_data: dict[str, Any],
    metrics: dict[str, Any],
    user_average: dict[str, float],
    platform: str,
) -> dict[str, Any]:
    """Generate AI-powered improvement recommendations for a post.

    Returns:
    {
        "improvement_recommendations": [...],
        "what_worked_well": [...],
        "what_needs_improvement": [...],
        "ai_analysis": {...}
    }
    """
    # Build context for LLM
    context = f"""
Post Performance Analysis Request:

Platform: {platform}
Content Type: {post_data.get('content_type', 'unknown')}
Message Angle: {post_data.get('message_angle', 'N/A')}

CURRENT METRICS:
- Likes: {metrics.get('likes', 0)}
- Comments: {metrics.get('comments', 0)}
- Shares: {metrics.get('shares', 0)}
- Views: {metrics.get('views', 0)}
- Saves: {metrics.get('saves', 0)}
- Reach: {metrics.get('reach', 0)}
- Engagement Score: {metrics.get('engagement_score', 0)}

USER'S AVERAGE PERFORMANCE ON {platform.upper()}:
- Avg Likes: {user_average.get('avg_likes', 0)}
- Avg Comments: {user_average.get('avg_comments', 0)}
- Avg Shares: {user_average.get('avg_shares', 0)}
- Avg Views: {user_average.get('avg_views', 0)}
- Avg Engagement: {user_average.get('avg_engagement_score', 0)}

COMPARISON:
- Likes vs Average: {((metrics.get('likes', 0) / max(user_average.get('avg_likes', 0), 1)) - 1) * 100:+.1f}%
- Comments vs Average: {((metrics.get('comments', 0) / max(user_average.get('avg_comments', 0), 1)) - 1) * 100:+.1f}%
- Shares vs Average: {((metrics.get('shares', 0) / max(user_average.get('avg_shares', 0), 1)) - 1) * 100:+.1f}%

POST DETAILS:
- Caption Length: {post_data.get('caption_length', 0)} characters
- Hashtag Count: {post_data.get('hashtag_count', 0)}
- Has Product Link: {post_data.get('has_product_link', False)}
- Media Type: {post_data.get('media_type', 'unknown')}
- Posted At: {post_data.get('posted_at', 'unknown')}

Analyze this post's performance and provide:
1. What worked well (3-5 specific points)
2. What needs improvement (3-5 specific actionable recommendations)
3. Specific changes to make for next post
"""

    # For now, return structured recommendations without LLM
    # TODO: Implement LLM-based analysis using llm.analyze_content_performance()

    recommendations = []
    worked_well = []
    needs_improvement = []

    # Analyze engagement rate
    current_engagement = metrics.get("likes", 0) + metrics.get("comments", 0) + metrics.get("shares", 0)
    avg_engagement = user_average.get("avg_engagement_score", 0)

    if current_engagement > avg_engagement * 1.2:
        worked_well.append(f"Strong engagement ({current_engagement} vs avg {avg_engagement:.0f})")
    elif current_engagement < avg_engagement * 0.8:
        needs_improvement.append("Low engagement compared to your average")
        recommendations.append("Try more compelling call-to-action in caption")

    # Analyze saves (content value indicator)
    if metrics.get("saves", 0) > user_average.get("avg_likes", 0) * 0.3:
        worked_well.append("High save rate - content provided value users want to revisit")
    elif metrics.get("saves", 0) < user_average.get("avg_likes", 0) * 0.1:
        needs_improvement.append("Low save rate - content may lack lasting value")
        recommendations.append("Add educational or actionable tips that users want to save")

    # Analyze comments (genuine engagement)
    comment_rate = metrics.get("comments", 0) / max(metrics.get("likes", 1), 1)
    if comment_rate > 0.1:  # More than 10% comment rate is excellent
        worked_well.append("High comment rate - sparked conversation")
    elif comment_rate < 0.02:
        needs_improvement.append("Low comment rate - not sparking conversation")
        recommendations.append("Ask questions or create discussion prompts in captions")

    # Analyze shares (viral potential)
    share_rate = metrics.get("shares", 0) / max(metrics.get("views", 1), 1)
    if share_rate > 0.05:
        worked_well.append("Strong share rate - highly shareable content")
    elif share_rate < 0.01:
        needs_improvement.append("Low share rate - content not inspiring shares")
        recommendations.append("Create more relatable or surprising content that people want to share")

    # Platform-specific recommendations
    if platform == "instagram":
        if metrics.get("reach", 0) < metrics.get("impressions", 1) * 0.3:
            needs_improvement.append("Low reach - algorithm not favoring this post")
            recommendations.append("Post during peak engagement hours (check insights for your audience)")

    if platform == "tiktok":
        if metrics.get("views", 0) < 300:
            needs_improvement.append("Low initial views - TikTok algorithm didn't push to FYP")
            recommendations.append("Use trending sounds and hooks in first 3 seconds")

    return {
        "improvement_recommendations": recommendations if recommendations else ["Performance is solid - keep up the good work!"],
        "what_worked_well": worked_well if worked_well else ["Post published successfully"],
        "what_needs_improvement": needs_improvement if needs_improvement else ["No major issues identified"],
        "ai_analysis": {
            "engagement_trend": "above_average" if current_engagement > avg_engagement else "below_average",
            "content_value_score": min(100, int((metrics.get("saves", 0) / max(metrics.get("likes", 1), 1)) * 100)),
            "virality_score": min(100, int((metrics.get("shares", 0) / max(metrics.get("views", 1), 1)) * 1000)),
            "conversation_score": min(100, int(comment_rate * 100)),
        },
    }


def analyze_post_performance(
    client: Client, *, post_id: str, force_reanalysis: bool = False
) -> dict[str, Any] | None:
    """Analyze a post's performance and store insights.

    Args:
        client: Supabase client
        post_id: Post ID to analyze
        force_reanalysis: Re-analyze even if already analyzed

    Returns:
        Content performance insight record or None if failed
    """
    # Check if already analyzed
    if not force_reanalysis:
        existing = (
            client.table("content_performance_insights")
            .select("*")
            .eq("post_id", post_id)
            .execute()
            .data
        )
        if existing:
            logger.info("Post %s already analyzed", post_id)
            return existing[0]

    # Get post details
    post = client.table("posts").select("*").eq("id", post_id).single().execute().data

    if not post or post.get("status") != "posted":
        logger.warning("Post %s not found or not posted yet", post_id)
        return None

    # Get variant and campaign
    variant = client.table("variants").select("*").eq("id", post["variant_id"]).single().execute().data
    campaign = client.table("campaigns").select("*").eq("id", variant["campaign_id"]).single().execute().data

    # Get caption
    caption = (
        client.table("captions")
        .select("*")
        .eq("variant_id", variant["id"])
        .eq("platform", post["platform"])
        .execute()
        .data
    )
    caption_text = caption[0].get("caption_text", "") if caption else ""
    hashtags = caption[0].get("hashtags", []) if caption else []

    # Get latest metrics
    latest_metrics = (
        client.table("post_metrics")
        .select("*")
        .eq("post_id", post_id)
        .order("fetched_at", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if not latest_metrics:
        logger.warning("No metrics found for post %s", post_id)
        return None

    metrics = latest_metrics[0]

    # Get user average performance
    user_avg = get_user_average_performance(
        client, user_id=campaign["user_id"], platform=post["platform"]
    )

    # Calculate engagement score
    engagement_score = metrics.get("likes", 0) + metrics.get("comments", 0) * 2 + metrics.get("shares", 0) * 3

    # Calculate performance tier and percentile
    # TODO: Get all user's engagement scores for percentile calculation
    performance_tier = calculate_performance_tier(engagement_score, user_avg.get("avg_engagement_score", 0))

    # Prepare post data for analysis
    post_data = {
        "content_type": campaign.get("campaign_type"),
        "message_angle": variant.get("message_angle"),
        "caption_length": len(caption_text),
        "hashtag_count": len(hashtags),
        "has_product_link": "http" in caption_text.lower(),
        "media_type": variant.get("media_type", "image"),
        "posted_at": post.get("posted_at"),
    }

    # Generate AI recommendations
    ai_insights = generate_improvement_recommendations(
        post_data=post_data,
        metrics=metrics,
        user_average=user_avg,
        platform=post["platform"],
    )

    # Calculate vs_user_average comparison
    vs_user_avg = {}
    if user_avg.get("avg_likes", 0) > 0:
        vs_user_avg["likes_diff_pct"] = round(
            ((metrics.get("likes", 0) / user_avg["avg_likes"]) - 1) * 100, 1
        )
    if user_avg.get("avg_comments", 0) > 0:
        vs_user_avg["comments_diff_pct"] = round(
            ((metrics.get("comments", 0) / user_avg["avg_comments"]) - 1) * 100, 1
        )
    if user_avg.get("avg_shares", 0) > 0:
        vs_user_avg["shares_diff_pct"] = round(
            ((metrics.get("shares", 0) / user_avg["avg_shares"]) - 1) * 100, 1
        )

    # Prepare insight record
    insight_record = {
        "post_id": post_id,
        "variant_id": variant["id"],
        "campaign_id": campaign["id"],
        "user_id": campaign["user_id"],
        "platform": post["platform"],
        "campaign_type": campaign["campaign_type"],
        "content_type": campaign.get("campaign_type"),  # TODO: Determine specific content type
        "message_angle": variant.get("message_angle"),
        "metrics": metrics,
        "engagement_score": engagement_score,
        "performance_tier": performance_tier,
        "performance_percentile": 50.0,  # TODO: Calculate actual percentile
        "posted_at": post.get("posted_at"),
        "best_posting_time_match": False,  # TODO: Compare with recommended posting time
        "day_of_week": datetime.fromisoformat(post["posted_at"].replace("Z", "+00:00")).strftime("%A") if post.get("posted_at") else None,
        "hour_of_day": datetime.fromisoformat(post["posted_at"].replace("Z", "+00:00")).hour if post.get("posted_at") else None,
        "caption_length": post_data["caption_length"],
        "hashtag_count": post_data["hashtag_count"],
        "has_product_link": post_data["has_product_link"],
        "media_type": post_data["media_type"],
        "ai_analysis": ai_insights.get("ai_analysis", {}),
        "improvement_recommendations": ai_insights.get("improvement_recommendations", []),
        "what_worked_well": ai_insights.get("what_worked_well", []),
        "what_needs_improvement": ai_insights.get("what_needs_improvement", []),
        "vs_user_average": vs_user_avg,
        "vs_platform_average": {},  # TODO: Add platform benchmarks
        "similar_posts_reference": [],  # TODO: Find similar high-performing posts
        "analysis_status": "analyzed",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Store or update insight
    if force_reanalysis and existing:
        result = (
            client.table("content_performance_insights")
            .update(insight_record)
            .eq("post_id", post_id)
            .execute()
        )
    else:
        result = client.table("content_performance_insights").insert(insight_record).execute()

    logger.info("Analyzed post %s - Performance: %s", post_id, performance_tier)

    return result.data[0] if result.data else None
