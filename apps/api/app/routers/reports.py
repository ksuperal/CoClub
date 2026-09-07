from fastapi import APIRouter, Depends, HTTPException

from ..db import get_current_user_id, get_service_client
from ..models.schemas import CampaignReportOut
from ..pipeline.step5_feedback import run_feedback_job

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
