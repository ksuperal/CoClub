"""Meta (Facebook Login for Business) OAuth — covers both Facebook Page posting and
Instagram posting, since an Instagram Business account posts via its linked Page's
access token. One connect flow, up to two `social_accounts` rows.

Requires a Meta Developer App with the "Facebook Login for Business" product, the
scopes below requested, Business Verification, and App Review before any account other
than a Tester/Admin on the app can complete this flow — see README.md.
"""

from typing import Any
from urllib.parse import urlencode

import httpx

from ..config import get_settings

# Not sent in the OAuth URL — Facebook Login for Business grants permissions via a saved
# "Login Configuration" (see config_id below) instead of a raw scope list. This documents
# what that Configuration in the app dashboard needs to include.
SCOPES = [
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "instagram_basic",
    "instagram_content_publish",
    "business_management",
]


def _graph_url(path: str) -> str:
    return f"https://graph.facebook.com/{get_settings().meta_graph_version}{path}"


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.meta_redirect_uri,
        "state": state,
        "config_id": settings.meta_login_config_id,
        "response_type": "code",
    }
    return f"https://www.facebook.com/{settings.meta_graph_version}/dialog/oauth?{urlencode(params)}"


def exchange_code_for_token(code: str) -> str:
    """Returns a short-lived user access token."""
    settings = get_settings()
    resp = httpx.get(
        _graph_url("/oauth/access_token"),
        params={
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "redirect_uri": settings.meta_redirect_uri,
            "code": code,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def exchange_long_lived_token(short_lived_token: str) -> str:
    """Exchanges a short-lived user token for one good ~60 days. Not the token we
    actually persist (that's the Page token below), but required to fetch Page tokens
    that stay valid for the long haul."""
    settings = get_settings()
    resp = httpx.get(
        _graph_url("/oauth/access_token"),
        params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "fb_exchange_token": short_lived_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_pages_and_ig_accounts(long_lived_user_token: str) -> list[dict[str, Any]]:
    """Page access tokens obtained this way don't expire under normal use (as long as
    the user keeps their Page role and doesn't revoke the app) — this is the token
    that's actually persisted and used for posting, not the user token above."""
    resp = httpx.get(
        _graph_url("/me/accounts"),
        params={
            "fields": "id,name,access_token,instagram_business_account{id,username}",
            "access_token": long_lived_user_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    pages = resp.json().get("data", [])

    result = []
    for page in pages:
        ig = page.get("instagram_business_account")
        result.append(
            {
                "page_id": page["id"],
                "page_name": page.get("name"),
                "page_token": page["access_token"],
                "ig_user_id": ig.get("id") if ig else None,
                "ig_username": ig.get("username") if ig else None,
            }
        )
    return result
