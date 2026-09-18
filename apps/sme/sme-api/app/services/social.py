"""Direct platform posting for Step 4 — Facebook Page, Instagram, and TikTok.

Replaces the earlier Ayrshare wrapper. Looks up the caller's connected account
(`social_accounts`, populated by the OAuth flow in routers/social.py); no connected
account for a platform still returns "pending_credentials" instead of raising, so the
pipeline runs end-to-end exactly as before for accounts that aren't connected yet.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from supabase import Client

from ..config import get_settings
from . import crypto, tiktok_oauth

logger = logging.getLogger(__name__)

TIKTOK_REFRESH_MARGIN = timedelta(minutes=5)


@dataclass
class PostResult:
    status: str  # "pending_credentials" | "posted" | "failed"
    external_post_id: str | None = None
    permalink: str | None = None
    error_message: str | None = None


def _full_caption(caption_text: str, hashtags: list[str]) -> str:
    if not hashtags:
        return caption_text
    return caption_text + "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in hashtags)


def _get_account(client: Client, *, user_id: str, platform: str) -> dict[str, Any] | None:
    rows = (
        client.table("social_accounts")
        .select("*")
        .eq("user_id", user_id)
        .eq("platform", platform)
        .eq("status", "connected")
        .execute()
        .data
    )
    return rows[0] if rows else None


def _refresh_tiktok_if_needed(client: Client, account: dict[str, Any]) -> dict[str, Any]:
    expires_at = account.get("token_expires_at")
    if not expires_at:
        return account
    expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_dt - datetime.now(timezone.utc) > TIKTOK_REFRESH_MARGIN:
        return account

    refresh_token = crypto.decrypt(account["refresh_token_encrypted"])
    tokens = tiktok_oauth.refresh_access_token(refresh_token)
    new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens["expires_in"])
    update = {
        "access_token_encrypted": crypto.encrypt(tokens["access_token"]),
        "refresh_token_encrypted": crypto.encrypt(tokens["refresh_token"]),  # tiktok rotates refresh tokens
        "token_expires_at": new_expires_at.isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    client.table("social_accounts").update(update).eq("id", account["id"]).execute()
    return {**account, **update}


def post_to_platform(
    client: Client,
    *,
    user_id: str,
    platform: str,
    caption_text: str,
    hashtags: list[str],
    image_url: str | None = None,
    media_type: str = "image",
    video_url: str | None = None,
) -> PostResult:
    """`media_type` picks image vs video posting per platform — each platform's video
    path is functionally distinct from its photo path (different endpoint/params/
    processing time), not a small tweak, so they're separate functions below."""
    account = _get_account(client, user_id=user_id, platform=platform)
    if account is None:
        return PostResult(status="pending_credentials")

    is_video = media_type == "video"
    if is_video and not video_url:
        return PostResult(status="failed", error_message="Video post requested but no video_url is set yet")

    try:
        if platform == "facebook":
            return _post_video_to_facebook(account, caption_text, hashtags, video_url) if is_video else _post_to_facebook(account, caption_text, hashtags, image_url)
        if platform == "instagram":
            return _post_video_to_instagram(account, caption_text, hashtags, video_url) if is_video else _post_to_instagram(account, caption_text, hashtags, image_url)
        if platform == "tiktok":
            account = _refresh_tiktok_if_needed(client, account)
            return _post_video_to_tiktok(account, caption_text, hashtags, video_url) if is_video else _post_to_tiktok(account, caption_text, hashtags, image_url)
        return PostResult(status="failed", error_message=f"Unsupported platform: {platform}")
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a failed post row, never raised
        logger.exception("Posting to %s failed", platform)
        return PostResult(status="failed", error_message=str(exc))


def _post_to_facebook(account: dict[str, Any], caption_text: str, hashtags: list[str], image_url: str) -> PostResult:
    settings = get_settings()
    page_token = crypto.decrypt(account["access_token_encrypted"])
    resp = httpx.post(
        f"https://graph.facebook.com/{settings.meta_graph_version}/{account['external_account_id']}/photos",
        data={"url": image_url, "caption": _full_caption(caption_text, hashtags), "access_token": page_token},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    post_id = data.get("post_id") or data.get("id")
    return PostResult(status="posted", external_post_id=post_id, permalink=f"https://facebook.com/{post_id}" if post_id else None)


def _post_video_to_facebook(account: dict[str, Any], caption_text: str, hashtags: list[str], video_url: str) -> PostResult:
    """Uses the `/{page_id}/videos` edge with `file_url` — Meta's simple (non-chunked)
    hosted-video-upload parameter. NOTE: unlike the photo path, this hasn't been
    verified against a live Page yet — Meta's resumable/chunked upload session is the
    documented path for larger files, and `file_url` may need to fall back to that for
    videos over a certain size. Flagged as a real open risk, not assumed solid."""
    settings = get_settings()
    page_token = crypto.decrypt(account["access_token_encrypted"])
    resp = httpx.post(
        f"https://graph-video.facebook.com/{settings.meta_graph_version}/{account['external_account_id']}/videos",
        data={"file_url": video_url, "description": _full_caption(caption_text, hashtags), "access_token": page_token},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    video_id = data.get("id")
    return PostResult(status="posted", external_post_id=video_id, permalink=f"https://facebook.com/{video_id}" if video_id else None)


def _post_to_instagram(account: dict[str, Any], caption_text: str, hashtags: list[str], image_url: str) -> PostResult:
    settings = get_settings()
    page_token = crypto.decrypt(account["access_token_encrypted"])
    ig_user_id = account["external_account_id"]
    base = f"https://graph.facebook.com/{settings.meta_graph_version}/{ig_user_id}"

    create_resp = httpx.post(
        f"{base}/media",
        data={"image_url": image_url, "caption": _full_caption(caption_text, hashtags), "access_token": page_token},
        timeout=30,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json()["id"]

    # Image containers are near-instant but not guaranteed synchronous — short poll before publish.
    for _ in range(5):
        status_resp = httpx.get(f"https://graph.facebook.com/{settings.meta_graph_version}/{creation_id}", params={"fields": "status_code", "access_token": page_token}, timeout=30)
        status_resp.raise_for_status()
        if status_resp.json().get("status_code") == "FINISHED":
            break
        time.sleep(2)

    publish_resp = httpx.post(f"{base}/media_publish", data={"creation_id": creation_id, "access_token": page_token}, timeout=30)
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]
    return PostResult(status="posted", external_post_id=media_id, permalink=f"https://www.instagram.com/p/{media_id}/")


# How long to keep polling an Instagram Reels container before giving up — video
# processing is meaningfully slower than a photo's near-instant container (Meta's own
# guidance: anywhere from ~30s to several minutes), so this budget is far longer than
# the photo path's handful of quick retries.
_REELS_POLL_MAX_SECONDS = 300
_REELS_POLL_INTERVAL_SECONDS = 10


def _post_video_to_instagram(account: dict[str, Any], caption_text: str, hashtags: list[str], video_url: str) -> PostResult:
    settings = get_settings()
    page_token = crypto.decrypt(account["access_token_encrypted"])
    ig_user_id = account["external_account_id"]
    base = f"https://graph.facebook.com/{settings.meta_graph_version}/{ig_user_id}"

    create_resp = httpx.post(
        f"{base}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": _full_caption(caption_text, hashtags),
            "access_token": page_token,
        },
        timeout=30,
    )
    create_resp.raise_for_status()
    creation_id = create_resp.json()["id"]

    elapsed = 0
    status_code = None
    while elapsed < _REELS_POLL_MAX_SECONDS:
        status_resp = httpx.get(
            f"https://graph.facebook.com/{settings.meta_graph_version}/{creation_id}",
            params={"fields": "status_code", "access_token": page_token},
            timeout=30,
        )
        status_resp.raise_for_status()
        status_code = status_resp.json().get("status_code")
        if status_code == "FINISHED":
            break
        if status_code == "ERROR":
            return PostResult(status="failed", error_message="Instagram Reels container processing failed")
        time.sleep(_REELS_POLL_INTERVAL_SECONDS)
        elapsed += _REELS_POLL_INTERVAL_SECONDS

    if status_code != "FINISHED":
        return PostResult(
            status="failed",
            error_message=f"Instagram Reels container never finished processing within {_REELS_POLL_MAX_SECONDS}s",
        )

    publish_resp = httpx.post(f"{base}/media_publish", data={"creation_id": creation_id, "access_token": page_token}, timeout=30)
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]
    return PostResult(status="posted", external_post_id=media_id, permalink=f"https://www.instagram.com/reel/{media_id}/")


def _tiktok_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}


def _tiktok_privacy_level(headers: dict[str, str]) -> str:
    # privacy_level can't be hardcoded — it's per-creator and can change, so it's queried fresh here.
    creator_resp = httpx.post(
        "https://open.tiktokapis.com/v2/post/publish/creator_info/query/", headers=headers, json={}, timeout=30
    )
    creator_resp.raise_for_status()
    privacy_options = creator_resp.json().get("data", {}).get("privacy_level_options", [])
    return privacy_options[0] if privacy_options else "SELF_ONLY"


def _tiktok_publish_result(data: dict[str, Any]) -> PostResult:
    if data.get("error", {}).get("code") not in (None, "ok"):
        return PostResult(status="failed", error_message=data["error"].get("message", "TikTok publish init failed"))

    # NOTE: TikTok's publish is async — this treats a successful `init` call as "posted"
    # (matching the same fire-and-forget optimism the old Ayrshare wrapper had). A fully
    # correct version would poll /v2/post/publish/status/fetch/ with publish_id before
    # marking the post row "posted". No public permalink is returned synchronously —
    # and while the app is unaudited, the post lands as private/draft regardless of the
    # privacy_level requested.
    publish_id = data.get("data", {}).get("publish_id")
    return PostResult(status="posted", external_post_id=publish_id, permalink=None)


def _post_to_tiktok(account: dict[str, Any], caption_text: str, hashtags: list[str], image_url: str) -> PostResult:
    access_token = crypto.decrypt(account["access_token_encrypted"])
    headers = _tiktok_headers(access_token)
    privacy_level = _tiktok_privacy_level(headers)

    body = {
        "media_type": "PHOTO",
        "post_mode": "DIRECT_POST",
        "post_info": {
            "title": _full_caption(caption_text, hashtags),
            "description": _full_caption(caption_text, hashtags),
            "privacy_level": privacy_level,
            "disable_comment": False,
            "auto_add_music": False,
        },
        "source_info": {"source": "PULL_FROM_URL", "photo_images": [image_url], "photo_cover_index": 0},
        "post_receive_flag": False,
    }
    resp = httpx.post("https://open.tiktokapis.com/v2/post/publish/content/init/", headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return _tiktok_publish_result(resp.json())


def _post_video_to_tiktok(account: dict[str, Any], caption_text: str, hashtags: list[str], video_url: str) -> PostResult:
    """Same `content/init` endpoint as the photo path, but `source_info.source:
    PULL_FROM_URL` takes `video_url` instead of `photo_images`, and `media_type` is
    dropped entirely — video is the endpoint's default mode, there's no
    `media_type: "VIDEO"` to set. Same domain-verification prerequisite as the photo
    path (the URL's domain must be verified in the TikTok developer dashboard) —
    should carry over since it's a property of the account/app, not the media type,
    but worth a real test rather than assuming."""
    access_token = crypto.decrypt(account["access_token_encrypted"])
    headers = _tiktok_headers(access_token)
    privacy_level = _tiktok_privacy_level(headers)

    body = {
        "post_mode": "DIRECT_POST",
        "post_info": {
            "title": _full_caption(caption_text, hashtags),
            "description": _full_caption(caption_text, hashtags),
            "privacy_level": privacy_level,
            "disable_comment": False,
            "auto_add_music": False,
        },
        "source_info": {"source": "PULL_FROM_URL", "video_url": video_url},
        "post_receive_flag": False,
    }
    resp = httpx.post("https://open.tiktokapis.com/v2/post/publish/content/init/", headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    return _tiktok_publish_result(resp.json())


def fetch_metrics(
    client: Client, *, user_id: str, platform: str, external_post_id: str, media_type: str = "image"
) -> dict[str, int] | None:
    """Fetches analytics for a posted item. Returns zeros only for the genuine "no
    data available" case (account not connected, or a platform — TikTok — that
    doesn't expose post insights at all). Returns None if the call itself failed
    (rate limit, network error, transient API failure) — this is NOT the same as
    zero engagement, and the caller (step5_feedback.refresh_metrics) must skip
    writing a snapshot rather than recording a false zero. A rate-limited request
    isn't retried here; the next scheduled poll a few hours later tries again
    naturally, which is already a form of backoff without extra retry logic.

    `media_type` picks the field set — verified live against a real posted video: a
    Facebook Video object is a different Graph API node type from a Page feed Post
    and rejects `shares` outright ("Tried accessing nonexisting field (shares)") but
    does expose a real `views` count that a photo post never had; Instagram Reels
    media rejects `likes`/`comments` as summary edges ("Tried accessing nonexisting
    field (likes)") and needs the flat `like_count`/`comments_count` fields instead.
    Getting this wrong doesn't surface as a visible error anywhere — it's a 400 that
    this function's own `except` swallows into a skipped snapshot, so a report that
    silently never accumulates data is the only symptom."""
    zeros = {"likes": 0, "comments": 0, "shares": 0, "views": 0}
    account = _get_account(client, user_id=user_id, platform=platform)
    if account is None:
        return zeros

    try:
        if platform == "facebook":
            token = crypto.decrypt(account["access_token_encrypted"])
            settings = get_settings()
            fields = (
                "likes.summary(true),comments.summary(true),views"
                if media_type == "video"
                else "likes.summary(true),comments.summary(true),shares"
            )
            resp = httpx.get(
                f"https://graph.facebook.com/{settings.meta_graph_version}/{external_post_id}",
                params={"fields": fields, "access_token": token},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
                "shares": data.get("shares", {}).get("count", 0),  # not requested/available for video — stays 0
                "views": data.get("views", 0),  # not requested/available for photos — stays 0
            }
        if platform == "instagram":
            token = crypto.decrypt(account["access_token_encrypted"])
            settings = get_settings()
            if media_type == "video":
                resp = httpx.get(
                    f"https://graph.facebook.com/{settings.meta_graph_version}/{external_post_id}",
                    params={"fields": "like_count,comments_count", "access_token": token},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "likes": data.get("like_count", 0),
                    "comments": data.get("comments_count", 0),
                    "shares": 0,  # not exposed on Reels media via this field set
                    "views": 0,
                }
            resp = httpx.get(
                f"https://graph.facebook.com/{settings.meta_graph_version}/{external_post_id}",
                params={"fields": "likes.summary(true),comments.summary(true),shares", "access_token": token},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "likes": data.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": data.get("comments", {}).get("summary", {}).get("total_count", 0),
                "shares": data.get("shares", {}).get("count", 0),
                "views": 0,
            }
        # TikTok's Content Posting API doesn't expose public post insights at all —
        # this is a genuine "no data available", not a failed call, so zeros is correct.
        return zeros
    except Exception:  # noqa: BLE001
        logger.exception("fetch_metrics failed for %s post %s", platform, external_post_id)
        return None
