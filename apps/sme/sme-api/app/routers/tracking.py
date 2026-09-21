"""Click and conversion tracking endpoints."""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..db import get_service_client
from ..services import conversions_api, utm_tracking

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tracking"])


class ClickEventData(BaseModel):
    """Click tracking payload."""
    url: str
    referrer: str | None = None
    user_agent: str | None = None


class ConversionEventData(BaseModel):
    """Conversion tracking payload."""
    event_name: str  # 'ViewContent', 'AddToCart', 'Purchase'
    event_time: int | None = None  # Unix timestamp, defaults to now
    url: str
    content_ids: list[str] | None = None
    value: float | None = None
    currency: str = "USD"
    num_items: int | None = None
    # Facebook browser cookies for better event matching
    fbp: str | None = None
    fbc: str | None = None


@router.post("/track/click")
async def track_click(request: Request, data: ClickEventData) -> dict[str, Any]:
    """Track a link click from social media.

    This endpoint should be called when a user clicks a UTM-tagged link
    from a social media post and lands on your website.

    Example usage from client-side:
    ```javascript
    fetch('/v1/track/click', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        url: window.location.href,
        referrer: document.referrer,
        user_agent: navigator.userAgent
      })
    });
    ```
    """
    client = get_service_client()

    # Extract UTM parameters from URL
    utm_params = utm_tracking.extract_utm_params(data.url)

    if not utm_params.get("utm_campaign"):
        return {
            "status": "ignored",
            "reason": "No UTM campaign parameter found in URL"
        }

    campaign_id = utm_params["utm_campaign"]
    variant_id = utm_params.get("utm_content")

    # Find post_id from variant_id
    post_id = None
    if variant_id:
        posts = (
            client.table("posts")
            .select("id")
            .eq("variant_id", variant_id)
            .limit(1)
            .execute()
            .data
        )
        if posts:
            post_id = posts[0]["id"]

    # Record click in database
    click_record = {
        "campaign_id": campaign_id,
        "post_id": post_id,
        "variant_id": variant_id,
        "utm_source": utm_params.get("utm_source"),
        "utm_medium": utm_params.get("utm_medium"),
        "utm_campaign": utm_params["utm_campaign"],
        "utm_content": utm_params.get("utm_content"),
        "clicked_url": data.url,
        "destination_url": data.url,
        "user_agent": data.user_agent,
        "ip_address": request.client.host if request.client else None,
        "referrer": data.referrer,
        "clicked_at": datetime.now(timezone.utc).isoformat(),
    }

    client.table("link_clicks").insert(click_record).execute()

    logger.info(
        "Tracked click for campaign %s from %s (post: %s)",
        campaign_id,
        utm_params.get("utm_source"),
        post_id
    )

    return {
        "status": "tracked",
        "campaign_id": campaign_id,
        "post_id": post_id,
        "utm_source": utm_params.get("utm_source")
    }


@router.post("/track/conversion")
async def track_conversion(request: Request, data: ConversionEventData) -> dict[str, Any]:
    """Track a conversion event (ViewContent, AddToCart, Purchase).

    This endpoint:
    1. Stores the conversion in your database (for campaign attribution)
    2. Sends the event to Meta Conversions API (for ad optimization)

    Example usage from client-side after purchase:
    ```javascript
    fetch('/v1/track/conversion', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        event_name: 'Purchase',
        url: window.location.href,
        content_ids: ['product_123'],
        value: 29.99,
        currency: 'USD',
        fbp: getCookie('_fbp'),  // Facebook browser pixel cookie
        fbc: getCookie('_fbc')   // Facebook click ID cookie
      })
    });
    ```
    """
    client = get_service_client()

    # Extract UTM parameters from URL
    utm_params = utm_tracking.extract_utm_params(data.url)
    campaign_id = utm_params.get("utm_campaign")
    variant_id = utm_params.get("utm_content")

    # Find post_id from variant_id
    post_id = None
    if variant_id:
        posts = (
            client.table("posts")
            .select("id")
            .eq("variant_id", variant_id)
            .limit(1)
            .execute()
            .data
        )
        if posts:
            post_id = posts[0]["id"]

    # Store conversion in database
    event_time = data.event_time or int(time.time())
    conversion_record = {
        "campaign_id": campaign_id,
        "post_id": post_id,
        "variant_id": variant_id,
        "event_type": data.event_name,
        "event_time": datetime.fromtimestamp(event_time, tz=timezone.utc).isoformat(),
        "content_ids": data.content_ids or [],
        "content_type": "product",
        "value": data.value,
        "currency": data.currency,
        "num_items": data.num_items or (len(data.content_ids) if data.content_ids else 0),
        "utm_source": utm_params.get("utm_source"),
        "utm_campaign": utm_params.get("utm_campaign"),
    }

    db_result = client.table("conversions").insert(conversion_record).execute()

    logger.info(
        "Tracked %s conversion for campaign %s: $%.2f (post: %s)",
        data.event_name,
        campaign_id,
        data.value or 0,
        post_id
    )

    # Also send to Meta Conversions API (server-side tracking)
    # This ensures the event is captured even if browser blocks the Pixel
    conversions_api_result = conversions_api.send_conversion_event(
        event_name=data.event_name,
        event_time=event_time,
        event_source_url=data.url,
        user_agent=data.user_agent or request.headers.get("user-agent", ""),
        user_ip=request.client.host if request.client else "127.0.0.1",
        fbp=data.fbp,
        fbc=data.fbc,
        content_ids=data.content_ids,
        value=data.value,
        currency=data.currency,
    )

    return {
        "status": "tracked",
        "campaign_id": campaign_id,
        "post_id": post_id,
        "event_name": data.event_name,
        "database": {"status": "success", "id": db_result.data[0]["id"] if db_result.data else None},
        "conversions_api": conversions_api_result,
    }


@router.get("/track/health")
def tracking_health() -> dict[str, Any]:
    """Check if tracking services are configured and healthy."""
    from ..config import get_settings
    settings = get_settings()

    return {
        "meta_pixel_configured": bool(
            hasattr(settings, 'meta_pixel_id') and settings.meta_pixel_id
        ),
        "conversions_api_configured": bool(
            hasattr(settings, 'meta_conversions_api_token') and settings.meta_conversions_api_token
        ),
        "database_connected": True,  # If we got here, database is working
    }
