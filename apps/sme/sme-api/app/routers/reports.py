from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..db import get_current_user_id, get_service_client
from ..models.schemas import CampaignReportOut
from ..pipeline.step5_feedback import run_feedback_job
from ..services import content_analysis

router = APIRouter(prefix="/campaigns", tags=["reports"])


@router.get("/{campaign_id}/report", response_model=CampaignReportOut | None)
def get_report(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    campaign = client.table("campaigns").select("id, user_id").eq("id", campaign_id).execute().data
    if not campaign or campaign[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    reports = (
        client.table("campaign_reports")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return reports[0] if reports else None


@router.post("/{campaign_id}/report/run-now", response_model=CampaignReportOut | None)
def run_report_now(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    """Manually trigger the feedback job instead of waiting 24hrs — for testing/verification."""
    client = get_service_client()
    campaign = client.table("campaigns").select("id, user_id").eq("id", campaign_id).execute().data
    if not campaign or campaign[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    run_feedback_job(campaign_id)

    reports = (
        client.table("campaign_reports")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
        .data
    )
    return reports[0] if reports else None


# Content Performance Analysis Endpoints


@router.post("/posts/{post_id}/analyze")
def analyze_post(
    post_id: str, force_reanalysis: bool = False, user_id: str = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Analyze a post's performance and generate improvement recommendations."""
    client = get_service_client()

    # Verify post belongs to user
    post = client.table("posts").select("variant_id").eq("id", post_id).single().execute().data
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    variant = client.table("variants").select("campaign_id").eq("id", post["variant_id"]).single().execute().data
    campaign = client.table("campaigns").select("user_id").eq("id", variant["campaign_id"]).single().execute().data

    if campaign["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Analyze post
    insight = content_analysis.analyze_post_performance(
        client, post_id=post_id, force_reanalysis=force_reanalysis
    )

    if not insight:
        raise HTTPException(status_code=400, detail="Failed to analyze post")

    return insight


@router.get("/posts/{post_id}/insights")
def get_post_insights(post_id: str, user_id: str = Depends(get_current_user_id)) -> dict[str, Any] | None:
    """Get existing performance insights for a post."""
    client = get_service_client()

    # Verify post belongs to user
    post = client.table("posts").select("variant_id").eq("id", post_id).single().execute().data
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    variant = client.table("variants").select("campaign_id").eq("id", post["variant_id"]).single().execute().data
    campaign = client.table("campaigns").select("user_id").eq("id", variant["campaign_id"]).single().execute().data

    if campaign["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get insights
    insights = client.table("content_performance_insights").select("*").eq("post_id", post_id).execute().data

    return insights[0] if insights else None


@router.get("/{campaign_id}/performance-insights")
def get_campaign_performance_insights(
    campaign_id: str, user_id: str = Depends(get_current_user_id)
) -> list[dict[str, Any]]:
    """Get all performance insights for posts in a campaign."""
    client = get_service_client()

    # Verify campaign belongs to user
    campaign = client.table("campaigns").select("user_id").eq("id", campaign_id).execute().data
    if not campaign or campaign[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get all insights for this campaign
    insights = (
        client.table("content_performance_insights")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("posted_at", desc=True)
        .execute()
        .data
    )

    return insights
