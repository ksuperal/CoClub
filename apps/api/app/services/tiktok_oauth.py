"""TikTok Content Posting API v2 OAuth.

Requires a TikTok Developer App with the Content Posting API product, the `video.publish`
scope requested (same scope name covers photo posting — there's no separate photo scope),
and an app audit before posts can go public. Until audited, posts land as private/draft,
visible only to the connecting account — see README.md.
"""

from typing import Any
from urllib.parse import urlencode

import httpx

from ..config import get_settings

SCOPES = ["user.info.basic", "video.publish"]

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_key": settings.tiktok_client_key,
        "redirect_uri": settings.tiktok_redirect_uri,
        "state": state,
        "scope": ",".join(SCOPES),
        "response_type": "code",
    }
    return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"


def exchange_code_for_token(code: str) -> dict[str, Any]:
    """Returns {access_token, expires_in, refresh_token, refresh_expires_in, open_id, scope}."""
    settings = get_settings()
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.tiktok_redirect_uri,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """Refresh tokens rotate — the caller must persist the new refresh_token too, not
    just the new access_token."""
    settings = get_settings()
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_key": settings.tiktok_client_key,
            "client_secret": settings.tiktok_client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_user_info(access_token: str) -> dict[str, Any]:
    resp = httpx.get(
        "https://open.tiktokapis.com/v2/user/info/",
        params={"fields": "open_id,display_name"},
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", {}).get("user", {})
