"""API endpoints for boosting posts via Meta Ads."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..db import get_current_user_id, get_service_client
from ..services import meta_ads, meta_oauth

router = APIRouter(prefix="/boost", tags=["boost"])


class ConnectAdAccountRequest(BaseModel):
    """Request to connect a Meta ad account."""
    platform: str = Field(..., description="'facebook' or 'instagram'")


class BoostPostRequest(BaseModel):
    """Request to boost a post."""
    ad_account_id: str = Field(..., description="UUID of ad_account from our database")
    objective: str = Field(default="OUTCOME_ENGAGEMENT", description="Campaign objective")
    budget_amount: float = Field(..., ge=1.0, description="Budget in dollars (minimum $1)")
    budget_type: str = Field(default="daily", description="'daily' or 'lifetime'")
    duration_days: int = Field(default=7, ge=1, le=30, description="How many days to run (1-30)")
    targeting: dict[str, Any] | None = Field(default=None, description="Audience targeting config")


class PauseBoostRequest(BaseModel):
    """Request to pause a boost."""
    boosted_post_id: str


class ResumeBoostRequest(BaseModel):
    """Request to resume a boost."""
    boosted_post_id: str


@router.get("/ad-accounts")
def list_ad_accounts(user_id: str = Depends(get_current_user_id)) -> list[dict[str, Any]]:
    """List all connected ad accounts for this user."""
    client = get_service_client()

    accounts = (
        client.table("ad_accounts")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return accounts


@router.post("/ad-accounts/connect")
def connect_ad_account(
    body: ConnectAdAccountRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Connect a Meta ad account by fetching available accounts from Meta API.

    This endpoint:
    1. Gets user's Meta access token
    2. Fetches all ad accounts from Meta
    3. Saves them to our database
    4. Returns the list of connected accounts
    """
    client = get_service_client()

    # Get user's Meta access token
    social_account = (
        client.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("platform", body.platform)
        .eq("status", "connected")
        .execute()
        .data
    )

    if not social_account:
        raise HTTPException(
            status_code=404,
            detail=f"No connected {body.platform} account found. Please connect your account first."
        )

    access_token = social_account[0].get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token not found. Please reconnect your account."
        )

    # Fetch ad accounts from Meta
    try:
        ad_accounts = meta_ads.get_ad_accounts(access_token=access_token)

        if not ad_accounts:
            raise HTTPException(
                status_code=404,
                detail="No ad accounts found. You need a Meta Ad Account to boost posts."
            )

        # Save all ad accounts
        saved_accounts = []
        for account in ad_accounts:
            saved = meta_ads.save_ad_account(
                client,
                user_id=user_id,
                platform=body.platform,
                account_data=account
            )
            saved_accounts.append(saved)

        return {
            "message": f"Successfully connected {len(saved_accounts)} ad account(s)",
            "accounts": saved_accounts
        }

    except meta_ads.MetaAdsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/posts/{post_id}/boost")
def boost_post(
    post_id: str,
    body: BoostPostRequest,
    user_id: str = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Boost a post by creating a Meta ad campaign.

    Steps:
    1. Verify post belongs to user
    2. Get user's Meta access token
    3. Create Meta Campaign → Ad Set → Ad
    4. Track boost in database
    5. Return boost details
    """
    client = get_service_client()

    # Verify post belongs to user
    post = client.table("posts").select("*, variant_id").eq("id", post_id).single().execute().data
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    variant = client.table("variants").select("campaign_id").eq("id", post["variant_id"]).single().execute().data
    campaign = client.table("campaigns").select("user_id").eq("id", variant["campaign_id"]).single().execute().data

    if campaign["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Verify post is published
    if post["status"] != "posted":
        raise HTTPException(status_code=400, detail="Can only boost published posts")

    # Verify ad account belongs to user
    ad_account = client.table("ad_accounts").select("*").eq("id", body.ad_account_id).single().execute().data
    if not ad_account or ad_account["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Ad account not found")

    # Get user's Meta access token
    platform = post["platform"]
    social_account = (
        client.table("social_accounts")
        .select("access_token")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .eq("status", "connected")
        .execute()
        .data
    )

    if not social_account:
        raise HTTPException(status_code=404, detail=f"No connected {platform} account found")

    access_token = social_account[0].get("access_token")

    # Create boost
    try:
        boost = meta_ads.boost_post(
            client,
            user_id=user_id,
            post_id=post_id,
            ad_account_id=body.ad_account_id,
            access_token=access_token,
            objective=body.objective,
            budget_amount=body.budget_amount,
            budget_type=body.budget_type,
            duration_days=body.duration_days,
            targeting=body.targeting,
        )

        return {
            "message": "Successfully boosted post",
            "boost": boost
        }

    except meta_ads.MetaAdsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts/{post_id}/boosts")
def list_post_boosts(
    post_id: str,
    user_id: str = Depends(get_current_user_id)
) -> list[dict[str, Any]]:
    """List all boosts for a specific post."""
    client = get_service_client()

    # Verify post belongs to user
    post = client.table("posts").select("variant_id").eq("id", post_id).single().execute().data
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    variant = client.table("variants").select("campaign_id").eq("id", post["variant_id"]).single().execute().data
    campaign = client.table("campaigns").select("user_id").eq("id", variant["campaign_id"]).single().execute().data

    if campaign["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get boosts
    boosts = (
        client.table("boosted_posts")
        .select("*")
        .eq("post_id", post_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return boosts


@router.post("/boosts/{boosted_post_id}/sync-metrics")
def sync_boost_metrics(
    boosted_post_id: str,
    user_id: str = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Sync performance metrics for a boosted post from Meta."""
    client = get_service_client()

    # Verify boost belongs to user
    boost = client.table("boosted_posts").select("*").eq("id", boosted_post_id).single().execute().data
    if not boost or boost["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Boosted post not found")

    # Get access token
    platform = boost["platform"]
    social_account = (
        client.table("social_accounts")
        .select("access_token")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .eq("status", "connected")
        .execute()
        .data
    )

    if not social_account:
        raise HTTPException(status_code=404, detail=f"No connected {platform} account found")

    access_token = social_account[0].get("access_token")

    # Sync metrics
    try:
        updated = meta_ads.sync_ad_metrics(
            client,
            boosted_post_id=boosted_post_id,
            access_token=access_token
        )

        return {
            "message": "Metrics synced successfully",
            "boost": updated
        }

    except meta_ads.MetaAdsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/boosts/{boosted_post_id}/pause")
def pause_boost(
    boosted_post_id: str,
    user_id: str = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Pause a boosted post ad campaign."""
    client = get_service_client()

    # Verify boost belongs to user
    boost = client.table("boosted_posts").select("*").eq("id", boosted_post_id).single().execute().data
    if not boost or boost["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Boosted post not found")

    # Get access token
    platform = boost["platform"]
    social_account = (
        client.table("social_accounts")
        .select("access_token")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .eq("status", "connected")
        .execute()
        .data
    )

    if not social_account:
        raise HTTPException(status_code=404, detail=f"No connected {platform} account found")

    access_token = social_account[0].get("access_token")

    # Pause
    try:
        updated = meta_ads.pause_boost(
            client,
            boosted_post_id=boosted_post_id,
            access_token=access_token
        )

        return {
            "message": "Boost paused successfully",
            "boost": updated
        }

    except meta_ads.MetaAdsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/boosts/{boosted_post_id}/resume")
def resume_boost(
    boosted_post_id: str,
    user_id: str = Depends(get_current_user_id)
) -> dict[str, Any]:
    """Resume a paused boosted post ad campaign."""
    client = get_service_client()

    # Verify boost belongs to user
    boost = client.table("boosted_posts").select("*").eq("id", boosted_post_id).single().execute().data
    if not boost or boost["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Boosted post not found")

    # Get access token
    platform = boost["platform"]
    social_account = (
        client.table("social_accounts")
        .select("access_token")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .eq("status", "connected")
        .execute()
        .data
    )

    if not social_account:
        raise HTTPException(status_code=404, detail=f"No connected {platform} account found")

    access_token = social_account[0].get("access_token")

    # Resume
    try:
        updated = meta_ads.resume_boost(
            client,
            boosted_post_id=boosted_post_id,
            access_token=access_token
        )

        return {
            "message": "Boost resumed successfully",
            "boost": updated
        }

    except meta_ads.MetaAdsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/campaigns/{campaign_id}/boosts")
def list_campaign_boosts(
    campaign_id: str,
    user_id: str = Depends(get_current_user_id)
) -> list[dict[str, Any]]:
    """List all boosted posts for a campaign."""
    client = get_service_client()

    # Verify campaign belongs to user
    campaign = client.table("campaigns").select("user_id").eq("id", campaign_id).execute().data
    if not campaign or campaign[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Get boosts
    boosts = (
        client.table("boosted_posts")
        .select("*")
        .eq("campaign_id", campaign_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return boosts
