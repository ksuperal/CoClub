"""Meta Conversions API integration for server-side conversion tracking."""

import hashlib
import logging
import time
from typing import Any

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)


def hash_user_data(value: str) -> str:
    """SHA256 hash for user data (email, phone, etc.) per Meta's requirements."""
    return hashlib.sha256(value.lower().strip().encode()).hexdigest()


def send_conversion_event(
    *,
    event_name: str,  # 'ViewContent', 'AddToCart', 'Purchase'
    event_time: int,  # Unix timestamp
    event_source_url: str,
    user_agent: str,
    user_ip: str,
    fbp: str | None = None,  # _fbp cookie from browser
    fbc: str | None = None,  # _fbc cookie from browser
    content_ids: list[str] | None = None,
    value: float | None = None,
    currency: str = "USD",
    **custom_data: Any,
) -> dict[str, Any]:
    """Send conversion event to Meta Conversions API.

    This provides server-side tracking as a complement to the Meta Pixel,
    ensuring events are captured even if the browser blocks the Pixel.
    """
    settings = get_settings()

    # Check if Meta Pixel is configured
    if not hasattr(settings, 'meta_pixel_id') or not settings.meta_pixel_id:
        logger.warning("META_PIXEL_ID not configured, skipping conversion tracking")
        return {"status": "skipped", "reason": "pixel_not_configured"}

    if not hasattr(settings, 'meta_conversions_api_token') or not settings.meta_conversions_api_token:
        logger.warning("META_CONVERSIONS_API_TOKEN not configured, skipping conversion tracking")
        return {"status": "skipped", "reason": "token_not_configured"}

    pixel_id = settings.meta_pixel_id
    access_token = settings.meta_conversions_api_token

    # Build event payload according to Conversions API spec
    event_data = {
        "event_name": event_name,
        "event_time": event_time,
        "action_source": "website",
        "event_source_url": event_source_url,
        "user_data": {
            "client_ip_address": user_ip,
            "client_user_agent": user_agent,
        },
    }

    # Add Facebook browser cookies if available (for better event matching)
    if fbp:
        event_data["user_data"]["fbp"] = fbp
    if fbc:
        event_data["user_data"]["fbc"] = fbc

    # Add custom data (product/purchase info)
    if content_ids or value:
        event_data["custom_data"] = {}
        if content_ids:
            event_data["custom_data"]["content_ids"] = content_ids
            event_data["custom_data"]["content_type"] = "product"
        if value is not None:
            event_data["custom_data"]["value"] = value
            event_data["custom_data"]["currency"] = currency
        # Add any additional custom data
        event_data["custom_data"].update(custom_data)

    # Prepare request payload
    payload = {
        "data": [event_data],
    }

    # Add test event code if in test mode
    if hasattr(settings, 'meta_pixel_test_code') and settings.meta_pixel_test_code:
        payload["test_event_code"] = settings.meta_pixel_test_code

    # Send to Conversions API
    try:
        resp = httpx.post(
            f"https://graph.facebook.com/v25.0/{pixel_id}/events",
            params={"access_token": access_token},
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        # Log success
        events_received = result.get("events_received", 0)
        logger.info(
            "Sent %s event to Conversions API: %d events received",
            event_name,
            events_received
        )

        return {"status": "success", "events_received": events_received, "result": result}

    except httpx.HTTPStatusError as e:
        logger.error(
            "Conversions API returned error %d: %s",
            e.response.status_code,
            e.response.text
        )
        return {"status": "error", "error": str(e)}

    except Exception as e:
        logger.exception("Failed to send conversion event to Meta")
        return {"status": "error", "error": str(e)}


def track_page_view(
    *,
    url: str,
    user_agent: str,
    user_ip: str,
    fbp: str | None = None,
    fbc: str | None = None,
) -> dict[str, Any]:
    """Track a page view event."""
    return send_conversion_event(
        event_name="PageView",
        event_time=int(time.time()),
        event_source_url=url,
        user_agent=user_agent,
        user_ip=user_ip,
        fbp=fbp,
        fbc=fbc,
    )


def track_view_content(
    *,
    url: str,
    user_agent: str,
    user_ip: str,
    product_id: str,
    product_name: str,
    value: float,
    currency: str = "USD",
    fbp: str | None = None,
    fbc: str | None = None,
) -> dict[str, Any]:
    """Track a product view event."""
    return send_conversion_event(
        event_name="ViewContent",
        event_time=int(time.time()),
        event_source_url=url,
        user_agent=user_agent,
        user_ip=user_ip,
        content_ids=[product_id],
        value=value,
        currency=currency,
        fbp=fbp,
        fbc=fbc,
        content_name=product_name,
    )


def track_add_to_cart(
    *,
    url: str,
    user_agent: str,
    user_ip: str,
    product_id: str,
    product_name: str,
    value: float,
    currency: str = "USD",
    fbp: str | None = None,
    fbc: str | None = None,
) -> dict[str, Any]:
    """Track an add to cart event."""
    return send_conversion_event(
        event_name="AddToCart",
        event_time=int(time.time()),
        event_source_url=url,
        user_agent=user_agent,
        user_ip=user_ip,
        content_ids=[product_id],
        value=value,
        currency=currency,
        fbp=fbp,
        fbc=fbc,
        content_name=product_name,
    )


def track_purchase(
    *,
    url: str,
    user_agent: str,
    user_ip: str,
    product_ids: list[str],
    value: float,
    currency: str = "USD",
    num_items: int = 1,
    fbp: str | None = None,
    fbc: str | None = None,
) -> dict[str, Any]:
    """Track a purchase/conversion event."""
    return send_conversion_event(
        event_name="Purchase",
        event_time=int(time.time()),
        event_source_url=url,
        user_agent=user_agent,
        user_ip=user_ip,
        content_ids=product_ids,
        value=value,
        currency=currency,
        fbp=fbp,
        fbc=fbc,
        num_items=num_items,
    )
