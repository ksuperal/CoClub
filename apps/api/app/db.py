from functools import lru_cache

from fastapi import Header, HTTPException
from supabase import Client, create_client

from .config import get_settings


@lru_cache
def get_service_client() -> Client:
    """Service-role client. Bypasses RLS — only use after verifying the caller's JWT
    via `get_current_user_id` and scoping every query/write to that user_id yourself."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """Verifies the caller's Supabase JWT (sent as `Authorization: Bearer <token>`)
    against Supabase Auth and returns the user id. Every route depends on this instead
    of trusting a client-supplied user_id."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    client = get_service_client()

    try:
        result = client.auth.get_user(token)
    except Exception as exc:  # noqa: BLE001 - surface as 401, not 500
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if not result or not result.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return result.user.id
