"""Track follower growth across social platforms."""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from supabase import Client

from ..config import get_settings
from . import crypto

logger = logging.getLogger(__name__)


def fetch_follower_count(
    client: Client, *, user_id: str, platform: str
) -> int | None:
    """Fetch current follower count for a social account."""
    # Get account
    account_rows = (
        client.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .eq("status", "connected")
        .execute()
        .data
    )

    if not account_rows:
        logger.warning("No connected %s account for user %s", platform, user_id)
        return None

    account = account_rows[0]
    token = crypto.decrypt(account["access_token_encrypted"])
    settings = get_settings()

    try:
        if platform == "instagram":
            # Instagram follower count
            resp = httpx.get(
                f"https://graph.facebook.com/{settings.meta_graph_version}/{account['external_account_id']}",
                params={"fields": "followers_count", "access_token": token},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("followers_count", 0)

        elif platform == "facebook":
            # Facebook Page fan count
            resp = httpx.get(
                f"https://graph.facebook.com/{settings.meta_graph_version}/{account['external_account_id']}",
                params={"fields": "fan_count", "access_token": token},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("fan_count", 0)

        elif platform == "tiktok":
            # TikTok follower count (requires user.info.stats scope)
            # Note: This scope requires approval from TikTok
            resp = httpx.post(
                "https://open.tiktokapis.com/v2/user/info/",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"fields": ["follower_count"]},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            user_data = data.get("data", {}).get("user", {})
            return user_data.get("follower_count", 0)

        else:
            logger.error("Unsupported platform for follower tracking: %s", platform)
            return None

    except Exception:
        logger.exception("Failed to fetch follower count for %s", platform)
        return None


def update_follower_count(client: Client, *, user_id: str, platform: str) -> bool:
    """Fetch and update follower count in database."""
    follower_count = fetch_follower_count(client, user_id=user_id, platform=platform)

    if follower_count is None:
        return False

    # Update the social_accounts table
    client.table("social_accounts").update({
        "follower_count": follower_count,
        "follower_count_updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("user_id", user_id).eq("platform", platform).execute()

    logger.info("Updated follower count for %s %s: %d", user_id, platform, follower_count)
    return True


def store_baseline_follower_counts(
    client: Client, *, campaign_id: str, user_id: str, platforms: list[str]
) -> dict[str, int]:
    """Store baseline follower counts for a campaign when it's posted.

    This captures the starting point for follower growth tracking.
    Returns the baseline counts that were stored.
    """
    baseline = {}

    for platform in platforms:
        # Get current follower count (already updated by update_follower_count)
        account = (
            client.table("social_accounts")
            .select("follower_count")
            .eq("user_id", user_id)
            .eq("platform", platform)
            .execute()
            .data
        )

        if account and account[0].get("follower_count") is not None:
            baseline[platform] = account[0]["follower_count"]

    # Store baseline in campaigns table
    if baseline:
        client.table("campaigns").update({
            "follower_baseline": baseline
        }).eq("id", campaign_id).execute()

        logger.info("Stored baseline follower counts for campaign %s: %s", campaign_id, baseline)

    return baseline


def calculate_campaign_follower_growth(
    client: Client, *, campaign_id: str
) -> dict[str, int]:
    """Calculate follower growth during a campaign period (24 hours).

    Fetches fresh follower counts from platform APIs, updates the database,
    then compares to baseline counts stored when campaign was posted.
    Returns dict with platform -> follower_growth (difference) mapping.

    Example: {"instagram": 45, "facebook": -2, "tiktok": 103}
    (positive = gained followers, negative = lost followers)
    """
    # Get campaign details including baseline
    campaign = client.table("campaigns").select("user_id, follower_baseline").eq("id", campaign_id).single().execute().data
    user_id = campaign["user_id"]
    baseline = campaign.get("follower_baseline") or {}

    if not baseline:
        logger.warning("No baseline follower counts for campaign %s", campaign_id)
        return {}

    growth = {}

    for platform, baseline_count in baseline.items():
        # Refresh and persist the current follower count (24 hours after posting)
        update_follower_count(client, user_id=user_id, platform=platform)

        # Fetch the updated count from database
        account = (
            client.table("social_accounts")
            .select("follower_count")
            .eq("user_id", user_id)
            .eq("platform", platform)
            .execute()
            .data
        )

        if account and account[0].get("follower_count") is not None:
            current_count = account[0]["follower_count"]
            # Calculate the difference (growth can be positive or negative)
            growth[platform] = current_count - baseline_count
            logger.info(
                "Campaign %s %s follower growth: %d -> %d = %+d",
                campaign_id, platform, baseline_count, current_count, growth[platform]
            )

    return growth
