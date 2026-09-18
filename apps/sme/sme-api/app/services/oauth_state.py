"""Signs/verifies the OAuth `state` param carried across the redirect to Meta/TikTok
and back. The callback is a plain browser navigation — no Authorization header — so this
is how `GET /social/callback/{platform}` knows which user is connecting and that the
request wasn't forged. Stdlib HMAC, no new dependency.
"""

import base64
import hashlib
import hmac
import json
import time

from ..config import get_settings

STATE_TTL_SECONDS = 600  # the whole connect flow (redirect out, consent, redirect back) has 10 minutes


def _secret() -> bytes:
    # Reusing the token-encryption key as the HMAC secret is fine — Fernet keys are
    # just secret bytes, and this is a separate use (signing, not encrypting).
    return get_settings().social_token_encryption_key.encode()


def _b64decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign_state(*, user_id: str, platform: str) -> str:
    payload = {"user_id": user_id, "platform": platform, "exp": int(time.time()) + STATE_TTL_SECONDS}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    sig = hmac.new(_secret(), body, hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=")
    return f"{body.decode()}.{sig_b64.decode()}"


def verify_state(state: str, *, platform: str) -> str:
    """Returns the user_id if valid, raises ValueError otherwise."""
    try:
        body_b64, sig_b64 = state.split(".", 1)
        body = _b64decode(body_b64)
        expected_sig = hmac.new(_secret(), body_b64.encode(), hashlib.sha256).digest()
        actual_sig = _b64decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("bad signature")

        payload = json.loads(body)
        if payload["platform"] != platform:
            raise ValueError("platform mismatch")
        if payload["exp"] < time.time():
            raise ValueError("expired")
        return payload["user_id"]
    except (ValueError, KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid OAuth state") from exc
