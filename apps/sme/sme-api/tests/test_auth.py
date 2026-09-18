"""Local JWT verification (db.get_current_user_id) and the service-caller primitive
(db.get_service_caller) added to close the "every request round-trips to Supabase
Auth" gap from the architecture review. Calls the async dependency functions directly
via asyncio.run rather than going through TestClient, so these stay pure unit tests
with no network dependency either way.
"""

import asyncio
import time

import jwt as pyjwt
import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.db import get_current_user_id, get_service_caller

TEST_SECRET = "unit-test-jwt-secret"


def _sign(payload: dict, secret: str = TEST_SECRET) -> str:
    return pyjwt.encode(payload, secret, algorithm="HS256")


def _future() -> int:
    return int(time.time()) + 3600


def _past() -> int:
    return int(time.time()) - 3600


@pytest.fixture
def jwt_secret_configured(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_jwt_secret", TEST_SECRET)
    return settings


@pytest.fixture
def service_keys_configured(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "service_api_keys", "key-a,key-b")
    return settings


def test_valid_local_token_returns_subject(jwt_secret_configured):
    token = _sign({"sub": "user-123", "aud": "authenticated", "exp": _future()})
    user_id = asyncio.run(get_current_user_id(authorization=f"Bearer {token}"))
    assert user_id == "user-123"


def test_expired_local_token_is_rejected(jwt_secret_configured):
    token = _sign({"sub": "user-123", "aud": "authenticated", "exp": _past()})
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user_id(authorization=f"Bearer {token}"))
    assert exc.value.status_code == 401


def test_tampered_local_token_is_rejected(jwt_secret_configured):
    token = _sign({"sub": "user-123", "aud": "authenticated", "exp": _future()}, secret="wrong-secret")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user_id(authorization=f"Bearer {token}"))
    assert exc.value.status_code == 401


def test_missing_bearer_header_is_rejected():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user_id(authorization=None))
    assert exc.value.status_code == 401


def test_valid_service_key_accepted(service_keys_configured):
    caller = asyncio.run(get_service_caller(x_service_key="key-a"))
    assert caller == "key-a"


def test_unknown_service_key_rejected(service_keys_configured):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_service_caller(x_service_key="not-a-real-key"))
    assert exc.value.status_code == 401


def test_missing_service_key_rejected(service_keys_configured):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_service_caller(x_service_key=None))
    assert exc.value.status_code == 401
