"""Symmetric encryption for social account tokens at rest.

Security-critical, unlike most of this app's "runs fine without the key" pattern —
these are live credentials that can post to a real customer's social accounts, so this
fails fast on a missing/malformed key instead of silently no-op'ing.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from ..config import get_settings


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().social_token_encryption_key
    try:
        return Fernet(key.encode())
    except Exception as exc:  # noqa: BLE001 - surfaced clearly, not swallowed
        raise ValueError(
            "SOCIAL_TOKEN_ENCRYPTION_KEY is missing or invalid. Generate one with: "
            'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        ) from exc


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt a stored social token — check SOCIAL_TOKEN_ENCRYPTION_KEY") from exc
