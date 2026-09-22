"""Meta Ads API service for boosting posts programmatically.

This service handles:
- Connecting Meta Ad Accounts
- Creating boosted post campaigns from organic posts
- Managing ad campaigns (pause, resume, update budget)
- Syncing ad performance metrics
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from supabase import Client

logger = logging.getLogger(__name__)

# Meta Graph API base URL
GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class MetaAdsError(Exception):
    """Base exception for Meta Ads API errors."""
    pass


def get_ad_accounts(*, access_token: str) -> list[dict[str, Any]]:
    """Fetch all ad accounts accessible to the user's access token.

    Args:
        access_token: User's Meta access token with ads_management permission

    Returns:
        List of ad accounts with id, name, account_id, currency, etc.

    Raises:
        MetaAdsError: If API call fails
    """
    url = f"{GRAPH_API_BASE}/me/adaccounts"
    params = {
        "access_token": access_token,
        "fields": "id,name,account_id,account_status,currency,timezone_name,amount_spent,balance,spend_cap"
    }

    try:
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        return data.get("data", [])

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch ad accounts: {e}")
        raise MetaAdsError(f"Failed to fetch ad accounts: {e}")


def save_ad_account(client: Client, *, user_id: str, platform: str, account_data: dict[str, Any]) -> dict[str, Any]:
    """Save or update ad account in database.

    Args:
        client: Supabase client
        user_id: User's ID
        platform: 'facebook' or 'instagram' (both use same Meta ad account)
        account_data: Ad account data from Meta API

    Returns:
        Saved ad_account record
    """
    # Extract ad account ID (remove 'act_' prefix for storage)
    external_id = account_data.get("id", "")

    record = {
        "user_id": user_id,
        "platform": platform,
        "external_ad_account_id": external_id,
        "external_ad_account_name": account_data.get("name"),
        "currency": account_data.get("currency", "USD"),
        "timezone": account_data.get("timezone_name"),
        "account_status": account_data.get("account_status"),
        "amount_spent": float(account_data.get("amount_spent", 0)) / 100,  # Meta returns in cents
        "balance": float(account_data.get("balance", 0)) / 100,
        "spend_cap": float(account_data.get("spend_cap", 0)) / 100 if account_data.get("spend_cap") else None,
        "last_synced_at": datetime.now(timezone.utc).isoformat(),
    }

    # Upsert (update if exists, insert if not)
    result = (
        client.table("ad_accounts")
        .upsert(record, on_conflict="user_id,platform,external_ad_account_id")
        .execute()
    )

    return result.data[0] if result.data else None


def boost_post(
    client: Client,
    *,
    user_id: str,
    post_id: str,
    ad_account_id: str,
    access_token: str,
    objective: str = "OUTCOME_ENGAGEMENT",
    budget_amount: float,
    budget_type: str = "daily",
    duration_days: int = 7,
    targeting: dict[str, Any] | None = None,
    boost_reason: str | None = None,
) -> dict[str, Any]:
    """Boost a post by creating a Meta ad campaign.

    Args:
        client: Supabase client
        user_id: User's ID
        post_id: Post ID to boost
        ad_account_id: UUID of ad_account in our database
        access_token: User's Meta access token
        objective: Campaign objective (OUTCOME_ENGAGEMENT, OUTCOME_TRAFFIC, OUTCOME_AWARENESS, etc.)
        budget_amount: Budget in dollars
        budget_type: 'daily' or 'lifetime'
        duration_days: How many days to run the boost
        targeting: Audience targeting dict (optional)
        boost_reason: AI explanation of why to boost this post

    Returns:
        boosted_posts record with external campaign/adset/ad IDs

    Raises:
        MetaAdsError: If any step of the boost creation fails
    """
    # Get post and ad account details
    post = client.table("posts").select("*, variant_id").eq("id", post_id).single().execute().data
    if not post:
        raise MetaAdsError(f"Post {post_id} not found")

    variant = client.table("variants").select("campaign_id").eq("id", post["variant_id"]).single().execute().data

    ad_account = client.table("ad_accounts").select("*").eq("id", ad_account_id).single().execute().data
    if not ad_account:
        raise MetaAdsError(f"Ad account {ad_account_id} not found")

    platform = post["platform"]
    external_ad_account_id = ad_account["external_ad_account_id"]

    # Get the organic post's external ID
    external_post_id = post.get("external_post_id")
    if not external_post_id:
        raise MetaAdsError(f"Post {post_id} has no external_post_id - cannot boost")

    # Create boosted_posts record (status: creating)
    boost_record = {
        "user_id": user_id,
        "post_id": post_id,
        "variant_id": post["variant_id"],
        "campaign_id": variant["campaign_id"],
        "ad_account_id": ad_account_id,
        "platform": platform,
        "objective": objective,
        "optimization_goal": "POST_ENGAGEMENT" if objective == "OUTCOME_ENGAGEMENT" else "LINK_CLICKS",
        "budget_type": budget_type,
        "budget_amount": budget_amount,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "targeting": targeting or {},
        "status": "creating",
        "boost_reason": boost_reason,
        "ai_suggested": boost_reason is not None,
    }

    boost = client.table("boosted_posts").insert(boost_record).execute().data[0]

    try:
        # Step 1: Create Campaign
        campaign_id = _create_campaign(
            access_token=access_token,
            ad_account_id=external_ad_account_id,
            name=f"Boost Post {post_id[:8]}",
            objective=objective,
        )

        # Step 2: Create Ad Set
        adset_id = _create_adset(
            access_token=access_token,
            ad_account_id=external_ad_account_id,
            campaign_id=campaign_id,
            name=f"Boost AdSet {post_id[:8]}",
            budget_amount=budget_amount,
            budget_type=budget_type,
            duration_days=duration_days,
            targeting=targeting,
            optimization_goal=boost_record["optimization_goal"],
        )

        # Step 3: Create Ad from organic post
        ad_id = _create_ad_from_post(
            access_token=access_token,
            ad_account_id=external_ad_account_id,
            adset_id=adset_id,
            post_id=external_post_id,
            name=f"Boost Ad {post_id[:8]}",
        )

        # Update boost record with external IDs and status
        updated_boost = (
            client.table("boosted_posts")
            .update({
                "external_campaign_id": campaign_id,
                "external_adset_id": adset_id,
                "external_ad_id": ad_id,
                "status": "active",
            })
            .eq("id", boost["id"])
            .execute()
            .data[0]
        )

        logger.info(f"Successfully boosted post {post_id} - Campaign: {campaign_id}, Ad: {ad_id}")
        return updated_boost

    except Exception as e:
        # Update boost record with error
        client.table("boosted_posts").update({
            "status": "failed",
            "error_message": str(e),
        }).eq("id", boost["id"]).execute()

        logger.error(f"Failed to boost post {post_id}: {e}")
        raise MetaAdsError(f"Failed to boost post: {e}")


def _create_campaign(
    *,
    access_token: str,
    ad_account_id: str,
    name: str,
    objective: str,
) -> str:
    """Create a Meta ad campaign.

    Returns:
        Campaign ID
    """
    url = f"{GRAPH_API_BASE}/{ad_account_id}/campaigns"

    payload = {
        "access_token": access_token,
        "name": name,
        "objective": objective,
        "status": "ACTIVE",
        "special_ad_categories": "[]",  # Required, empty for non-special ads
    }

    try:
        response = httpx.post(url, data=payload, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        return data["id"]

    except httpx.HTTPError as e:
        logger.error(f"Failed to create campaign: {e}")
        raise MetaAdsError(f"Failed to create campaign: {e}")


def _create_adset(
    *,
    access_token: str,
    ad_account_id: str,
    campaign_id: str,
    name: str,
    budget_amount: float,
    budget_type: str,
    duration_days: int,
    targeting: dict[str, Any] | None,
    optimization_goal: str,
) -> str:
    """Create a Meta ad set.

    Returns:
        Ad Set ID
    """
    url = f"{GRAPH_API_BASE}/{ad_account_id}/adsets"

    # Calculate budget in cents
    budget_cents = int(budget_amount * 100)

    # Set start and end times
    start_time = datetime.now(timezone.utc)
    end_time = datetime.fromtimestamp(start_time.timestamp() + (duration_days * 24 * 60 * 60), tz=timezone.utc)

    # Default targeting if none provided
    if not targeting:
        targeting = {
            "geo_locations": {"countries": ["US"]},
            "age_min": 18,
            "age_max": 65,
        }

    payload = {
        "access_token": access_token,
        "name": name,
        "campaign_id": campaign_id,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": optimization_goal,
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "status": "ACTIVE",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "targeting": targeting,
    }

    # Add budget (daily or lifetime)
    if budget_type == "daily":
        payload["daily_budget"] = budget_cents
    else:
        payload["lifetime_budget"] = budget_cents

    try:
        response = httpx.post(url, json=payload, params={"access_token": access_token}, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        return data["id"]

    except httpx.HTTPError as e:
        logger.error(f"Failed to create ad set: {e}")
        raise MetaAdsError(f"Failed to create ad set: {e}")


def _create_ad_from_post(
    *,
    access_token: str,
    ad_account_id: str,
    adset_id: str,
    post_id: str,
    name: str,
) -> str:
    """Create an ad from an existing organic post.

    Args:
        post_id: The external post ID (page_id_postid format)

    Returns:
        Ad ID
    """
    url = f"{GRAPH_API_BASE}/{ad_account_id}/ads"

    # Create ad creative from existing post
    creative = {
        "object_story_id": post_id,  # Use the organic post directly
    }

    payload = {
        "access_token": access_token,
        "name": name,
        "adset_id": adset_id,
        "creative": creative,
        "status": "ACTIVE",
    }

    try:
        response = httpx.post(url, json=payload, params={"access_token": access_token}, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        return data["id"]

    except httpx.HTTPError as e:
        logger.error(f"Failed to create ad from post: {e}")
        raise MetaAdsError(f"Failed to create ad from post: {e}")


def sync_ad_metrics(client: Client, *, boosted_post_id: str, access_token: str) -> dict[str, Any]:
    """Sync performance metrics for a boosted post from Meta Ads API.

    Args:
        client: Supabase client
        boosted_post_id: UUID of boosted_posts record
        access_token: User's Meta access token

    Returns:
        Updated boosted_posts record
    """
    boost = client.table("boosted_posts").select("*").eq("id", boosted_post_id).single().execute().data
    if not boost:
        raise MetaAdsError(f"Boosted post {boosted_post_id} not found")

    ad_id = boost.get("external_ad_id")
    if not ad_id:
        raise MetaAdsError(f"Boosted post {boosted_post_id} has no external_ad_id")

    # Fetch ad insights
    url = f"{GRAPH_API_BASE}/{ad_id}/insights"
    params = {
        "access_token": access_token,
        "fields": "impressions,reach,clicks,actions,spend,cpm,cpc,ctr",
    }

    try:
        response = httpx.get(url, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        if not data.get("data"):
            logger.warning(f"No insights data for ad {ad_id} yet")
            return boost

        insights = data["data"][0]

        # Extract metrics
        impressions = int(insights.get("impressions", 0))
        reach = int(insights.get("reach", 0))
        clicks = int(insights.get("clicks", 0))
        spend = float(insights.get("spend", 0))
        cpm = float(insights.get("cpm", 0))
        cpc = float(insights.get("cpc", 0))
        ctr = float(insights.get("ctr", 0))

        # Extract engagement and conversions from actions
        engagement = 0
        conversions = 0
        actions = insights.get("actions", [])
        for action in actions:
            action_type = action.get("action_type")
            value = int(action.get("value", 0))

            if action_type == "post_engagement":
                engagement = value
            elif action_type in ["offsite_conversion", "purchase"]:
                conversions += value

        # Update boost record
        updated = (
            client.table("boosted_posts")
            .update({
                "impressions": impressions,
                "reach": reach,
                "clicks": clicks,
                "engagement": engagement,
                "conversions": conversions,
                "amount_spent": spend,
                "cpm": cpm,
                "cpc": cpc,
                "ctr": ctr,
                "last_metrics_sync": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", boosted_post_id)
            .execute()
            .data[0]
        )

        logger.info(f"Synced metrics for boosted post {boosted_post_id}: {impressions} impressions, ${spend} spent")
        return updated

    except httpx.HTTPError as e:
        logger.error(f"Failed to sync ad metrics: {e}")
        raise MetaAdsError(f"Failed to sync ad metrics: {e}")


def pause_boost(client: Client, *, boosted_post_id: str, access_token: str) -> dict[str, Any]:
    """Pause a boosted post ad campaign.

    Args:
        client: Supabase client
        boosted_post_id: UUID of boosted_posts record
        access_token: User's Meta access token

    Returns:
        Updated boosted_posts record
    """
    boost = client.table("boosted_posts").select("*").eq("id", boosted_post_id).single().execute().data
    if not boost:
        raise MetaAdsError(f"Boosted post {boosted_post_id} not found")

    ad_id = boost.get("external_ad_id")
    if not ad_id:
        raise MetaAdsError(f"Boosted post has no external_ad_id")

    # Update ad status to PAUSED
    url = f"{GRAPH_API_BASE}/{ad_id}"
    payload = {
        "access_token": access_token,
        "status": "PAUSED",
    }

    try:
        response = httpx.post(url, data=payload, timeout=30.0)
        response.raise_for_status()

        # Update local record
        updated = (
            client.table("boosted_posts")
            .update({"status": "paused"})
            .eq("id", boosted_post_id)
            .execute()
            .data[0]
        )

        logger.info(f"Paused boosted post {boosted_post_id}")
        return updated

    except httpx.HTTPError as e:
        logger.error(f"Failed to pause ad: {e}")
        raise MetaAdsError(f"Failed to pause ad: {e}")


def resume_boost(client: Client, *, boosted_post_id: str, access_token: str) -> dict[str, Any]:
    """Resume a paused boosted post ad campaign.

    Args:
        client: Supabase client
        boosted_post_id: UUID of boosted_posts record
        access_token: User's Meta access token

    Returns:
        Updated boosted_posts record
    """
    boost = client.table("boosted_posts").select("*").eq("id", boosted_post_id).single().execute().data
    if not boost:
        raise MetaAdsError(f"Boosted post {boosted_post_id} not found")

    ad_id = boost.get("external_ad_id")
    if not ad_id:
        raise MetaAdsError(f"Boosted post has no external_ad_id")

    # Update ad status to ACTIVE
    url = f"{GRAPH_API_BASE}/{ad_id}"
    payload = {
        "access_token": access_token,
        "status": "ACTIVE",
    }

    try:
        response = httpx.post(url, data=payload, timeout=30.0)
        response.raise_for_status()

        # Update local record
        updated = (
            client.table("boosted_posts")
            .update({"status": "active"})
            .eq("id", boosted_post_id)
            .execute()
            .data[0]
        )

        logger.info(f"Resumed boosted post {boosted_post_id}")
        return updated

    except httpx.HTTPError as e:
        logger.error(f"Failed to resume ad: {e}")
        raise MetaAdsError(f"Failed to resume ad: {e}")
