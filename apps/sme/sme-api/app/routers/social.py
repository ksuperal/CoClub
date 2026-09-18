"""Connect-your-account OAuth flow for direct social posting (Step 4).

"facebook" is the connect trigger for both Facebook and Instagram — one Meta OAuth grant
can produce up to two `social_accounts` rows (a Page always gets a facebook row; if that
Page has a linked Instagram Business account, an instagram row is added too), since IG
posting piggybacks on the Page's access token. TikTok is a separate connect flow.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from supabase import Client

from ..config import get_settings
from ..db import get_current_user_id, get_service_client
from ..models.schemas import Platform, PostingTimeRecommendation
from ..services import crypto, meta_oauth, oauth_state, posting_time, tiktok_oauth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["social"])

ConnectPlatform = Literal["facebook", "tiktok"]

_ACCOUNT_COLUMNS = "id, platform, external_account_id, external_account_name, status, connected_at, updated_at"


@router.get("/social/accounts")
def list_accounts(user_id: str = Depends(get_current_user_id)) -> list[dict[str, Any]]:
    client = get_service_client()
    return client.table("social_accounts").select(_ACCOUNT_COLUMNS).eq("user_id", user_id).execute().data


@router.post("/social/connect/{platform}")
def connect(platform: ConnectPlatform, user_id: str = Depends(get_current_user_id)) -> dict[str, str]:
    settings = get_settings()
    if not settings.social_token_encryption_key:
        raise HTTPException(status_code=503, detail="SOCIAL_TOKEN_ENCRYPTION_KEY isn't configured yet")
    state = oauth_state.sign_state(user_id=user_id, platform=platform)

    if platform == "facebook":
        if not settings.meta_oauth_enabled:
            raise HTTPException(status_code=503, detail="Meta OAuth isn't configured yet (META_APP_ID/META_APP_SECRET/META_REDIRECT_URI)")
        return {"authorize_url": meta_oauth.build_authorize_url(state)}

    if not settings.tiktok_oauth_enabled:
        raise HTTPException(status_code=503, detail="TikTok OAuth isn't configured yet (TIKTOK_CLIENT_KEY/TIKTOK_CLIENT_SECRET/TIKTOK_REDIRECT_URI)")
    return {"authorize_url": tiktok_oauth.build_authorize_url(state)}


def _upsert_account(client: Client, *, user_id: str, platform: str, external_account_id: str, **fields: Any) -> None:
    row = {
        "user_id": user_id,
        "platform": platform,
        "external_account_id": external_account_id,
        "status": "connected",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    client.table("social_accounts").upsert(row, on_conflict="user_id,platform").execute()


@router.get("/social/callback/facebook")
def callback_facebook(code: str | None = None, state: str | None = None, error: str | None = None):
    settings = get_settings()
    frontend = settings.frontend_url

    if error or not code or not state:
        return RedirectResponse(f"{frontend}/settings/social?error={error or 'missing_code'}")

    try:
        user_id = oauth_state.verify_state(state, platform="facebook")
    except ValueError:
        return RedirectResponse(f"{frontend}/settings/social?error=invalid_state")

    try:
        short_token = meta_oauth.exchange_code_for_token(code)
        long_token = meta_oauth.exchange_long_lived_token(short_token)
        pages = meta_oauth.fetch_pages_and_ig_accounts(long_token)
    except Exception:  # noqa: BLE001
        logger.exception("Meta OAuth exchange failed")
        return RedirectResponse(f"{frontend}/settings/social?error=meta_exchange_failed")

    if not pages:
        return RedirectResponse(f"{frontend}/settings/social?error=no_pages_found")

    # MVP simplification: multiple Pages aren't disambiguated in the UI yet — take the
    # first one returned. A future picker would slot in right here.
    page = pages[0]
    client = get_service_client()

    _upsert_account(
        client,
        user_id=user_id,
        platform="facebook",
        external_account_id=page["page_id"],
        external_account_name=page["page_name"],
        access_token_encrypted=crypto.encrypt(page["page_token"]),
        platform_metadata={},
    )

    connected = "facebook"
    if page["ig_user_id"]:
        _upsert_account(
            client,
            user_id=user_id,
            platform="instagram",
            external_account_id=page["ig_user_id"],
            external_account_name=page["ig_username"],
            access_token_encrypted=crypto.encrypt(page["page_token"]),  # IG posts via the Page's token
            platform_metadata={"page_id": page["page_id"]},
        )
        connected = "facebook,instagram"

    return RedirectResponse(f"{frontend}/settings/social?connected={connected}")


@router.get("/social/callback/tiktok")
def callback_tiktok(code: str | None = None, state: str | None = None, error: str | None = None):
    settings = get_settings()
    frontend = settings.frontend_url

    if error or not code or not state:
        return RedirectResponse(f"{frontend}/settings/social?error={error or 'missing_code'}")

    try:
        user_id = oauth_state.verify_state(state, platform="tiktok")
    except ValueError:
        return RedirectResponse(f"{frontend}/settings/social?error=invalid_state")

    try:
        tokens = tiktok_oauth.exchange_code_for_token(code)
        user_info = tiktok_oauth.fetch_user_info(tokens["access_token"])
    except Exception:  # noqa: BLE001
        logger.exception("TikTok OAuth exchange failed")
        return RedirectResponse(f"{frontend}/settings/social?error=tiktok_exchange_failed")

    expires_at = datetime.now(timezone.utc).timestamp() + tokens["expires_in"]
    client = get_service_client()
    _upsert_account(
        client,
        user_id=user_id,
        platform="tiktok",
        external_account_id=tokens["open_id"],
        external_account_name=user_info.get("display_name"),
        access_token_encrypted=crypto.encrypt(tokens["access_token"]),
        refresh_token_encrypted=crypto.encrypt(tokens["refresh_token"]),
        token_expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat(),
    )

    return RedirectResponse(f"{frontend}/settings/social?connected=tiktok")


@router.get("/social/posting-time-recommendation/{platform}", response_model=PostingTimeRecommendation)
def get_posting_time_recommendation(platform: Platform, user_id: str = Depends(get_current_user_id)):
    """Not surfaced in the UI yet — gated behind a minimum amount of real posting
    history (see services/posting_time.py). Returns confidence: "insufficient_data"
    for everyone today; that's expected, not a bug."""
    client = get_service_client()
    return posting_time.recommend_posting_hour(client, user_id=user_id, platform=platform)


@router.delete("/social/accounts/{account_id}", status_code=204)
def disconnect(account_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    existing = client.table("social_accounts").select("id").eq("id", account_id).eq("user_id", user_id).execute().data
    if not existing:
        raise HTTPException(status_code=404, detail="Social account not found")
    client.table("social_accounts").delete().eq("id", account_id).execute()
