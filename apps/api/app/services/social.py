"""Ayrshare wrapper for Step 4 posting.

Gated on AYRSHARE_API_KEY: if it's unset (no account yet), post() returns a
"pending_credentials" result instead of calling the API, so the pipeline still runs
end-to-end. The moment a key is added, posting activates with no code changes.
"""

from dataclasses import dataclass

import httpx

from ..config import get_settings

AYRSHARE_POST_URL = "https://app.ayrshare.com/api/post"


@dataclass
class PostResult:
    status: str  # "pending_credentials" | "posted" | "failed"
    external_post_id: str | None = None
    permalink: str | None = None
    error_message: str | None = None


def post_to_platform(*, platform: str, caption_text: str, hashtags: list[str], image_url: str) -> PostResult:
    settings = get_settings()
    if not settings.ayrshare_enabled:
        return PostResult(status="pending_credentials")

    full_caption = caption_text
    if hashtags:
        full_caption += "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)

    payload = {
        "post": full_caption,
        "platforms": [platform],
        "mediaUrls": [image_url],
    }
    headers = {"Authorization": f"Bearer {settings.ayrshare_api_key}"}

    try:
        resp = httpx.post(AYRSHARE_POST_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        post_ids = data.get("postIds", [])
        post_id = post_ids[0]["id"] if post_ids else data.get("id")
        permalink = post_ids[0].get("postUrl") if post_ids else None
        return PostResult(status="posted", external_post_id=post_id, permalink=permalink)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a failed post row
        return PostResult(status="failed", error_message=str(exc))


def fetch_metrics(external_post_id: str) -> dict:
    """Fetches analytics for a posted item. Returns zeros if Ayrshare isn't configured
    or the call fails — Step 5 treats that as "no data yet", not fabricated numbers."""
    settings = get_settings()
    if not settings.ayrshare_enabled:
        return {"likes": 0, "comments": 0, "shares": 0, "views": 0}

    headers = {"Authorization": f"Bearer {settings.ayrshare_api_key}"}
    try:
        resp = httpx.get(
            "https://app.ayrshare.com/api/analytics/post",
            params={"id": external_post_id},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        analytics = data.get("analytics", data)
        return {
            "likes": analytics.get("likeCount", 0),
            "comments": analytics.get("commentCount", 0),
            "shares": analytics.get("shareCount", 0),
            "views": analytics.get("viewCount", analytics.get("impressionCount", 0)),
        }
    except Exception:  # noqa: BLE001
        return {"likes": 0, "comments": 0, "shares": 0, "views": 0}
