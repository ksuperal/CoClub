"""ElevenLabs Music generation — background music bed for video variants.

Synchronous, like OpenAI TTS — POST /v1/music returns the audio bytes directly
in the response body, no job/poll pattern (unlike Luma video). Verified against
ElevenLabs' current API reference (docs.elevenlabs.io/api-reference/music).
"""

import httpx

from ..config import get_settings

MODEL_ID = "music_v2_5"

MIN_LENGTH_MS = 3000
MAX_LENGTH_MS = 600_000


def _headers() -> dict[str, str]:
    return {"xi-api-key": get_settings().elevenlabs_api_key or ""}


def generate_music(prompt: str, *, length_ms: int) -> bytes:
    """Generates a short instrumental bed from a text prompt. `length_ms` is
    clamped to ElevenLabs' documented range (3s-10min) — callers pass the target
    video's duration, which is always far below that ceiling, but a variant
    generated with an unexpectedly short/long duration shouldn't 400 outright."""
    settings = get_settings()
    clamped_length = max(MIN_LENGTH_MS, min(length_ms, MAX_LENGTH_MS))

    resp = httpx.post(
        f"{settings.elevenlabs_base_url}/music",
        headers={**_headers(), "Content-Type": "application/json"},
        params={"output_format": "mp3_44100_128"},
        json={
            "prompt": prompt,
            "music_length_ms": clamped_length,
            "model_id": MODEL_ID,
            "force_instrumental": True,  # a spoken voiceover already carries the words — the bed should never compete with lyrics
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.content
