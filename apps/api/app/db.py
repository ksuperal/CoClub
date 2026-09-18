from functools import lru_cache

import jwt as pyjwt
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
    """Verifies the caller's Supabase JWT (sent as `Authorization: Bearer <token>`) and
    returns the user id. Every route depends on this instead of trusting a
    client-supplied user_id.

    With `SUPABASE_JWT_SECRET` set, verifies locally (HS256) — no network call, only
    works for Supabase projects still on the legacy shared JWT secret. Without it,
    falls back to a live round-trip against Supabase Auth (`client.auth.get_user`),
    which also covers projects on the newer asymmetric signing-key setup."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1]
    settings = get_settings()

    if settings.supabase_jwt_secret:
        try:
            payload = pyjwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except pyjwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
        return payload["sub"]

    client = get_service_client()

    try:
        result = client.auth.get_user(token)
    except Exception as exc:  # noqa: BLE001 - surface as 401, not 500
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    if not result or not result.user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return result.user.id


async def get_service_caller(x_service_key: str | None = Header(default=None)) -> str:
    """Verifies a machine-to-machine caller via a shared `X-Service-Key` header, checked
    against `SERVICE_API_KEYS` — separate from end-user Supabase JWTs. Not wired into
    any route yet; a reusable primitive for whatever a future second/third component
    needs to call in on, once that shape is known."""
    valid_keys = get_settings().service_api_keys_set
    if not x_service_key or x_service_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Missing or invalid service key")
    return x_service_key
