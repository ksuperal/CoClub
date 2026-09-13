"""ElevenLabs text-to-speech — voiceover for video variants.

Replaces OpenAI's gpt-4o-mini-tts (services/openai_tts.py, now unused/removed):
ElevenLabs' `eleven_v3` model is "our most emotionally rich, expressive speech
synthesis model" per their own docs, chosen specifically because gpt-4o-mini-tts's
output read as flat/monotone in practice even with steering instructions.

The control mechanism is genuinely different from OpenAI's, not just a different
vendor for the same shape of call: eleven_v3 has no separate freeform
"instructions" parameter. Expressiveness instead comes from two places —
1. Inline audio tags written directly INTO the script text (e.g. "[excited] Big
   news! [sighs] Finally, some calm.") — this is why llm.write_audio_script asks
   Claude to embed tags in voiceover_script itself, not in a side-channel string.
2. `stability` (lower = more emotional range, higher = flatter/more monotone —
   deliberately set below ElevenLabs' own 0.5 default here, since "monotone" was
   the exact complaint that triggered this switch).

Synchronous, like OpenAI TTS and ElevenLabs Music — POST returns audio bytes
directly, no job/poll pattern.
"""

import httpx

from ..config import get_settings

MODEL_ID = "eleven_v3"

# Deliberately below ElevenLabs' own 0.5 default — their docs are explicit that
# "higher values can result in a monotonous voice with limited emotion," which is
# exactly the failure mode this switch exists to fix.
STABILITY = 0.35
STYLE = 0.3

# Real, current premade voice confirmed directly from ElevenLabs' own docs
# (quickstart guide) — used only if this campaign's brand has no voice_id yet
# (pre-ElevenLabs brands, or list_premade_voices() failing at brand-intake time).
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # "George"


def _headers() -> dict[str, str]:
    return {"xi-api-key": get_settings().elevenlabs_api_key or ""}


def list_premade_voices(*, limit: int = 30) -> list[dict[str, str]]:
    """Fetches ElevenLabs' premade voice library so llm.choose_brand_voice can
    pick a real, current voice_id rather than a hardcoded (and possibly stale)
    one. Returns [{voice_id, name, description}, ...]. Raises on failure — the
    caller (step1_intake.py) treats that as non-fatal and falls back to
    DEFAULT_VOICE_ID instead of blocking brand creation on it."""
    settings = get_settings()
    resp = httpx.get(
        f"{settings.elevenlabs_base_url.replace('/v1', '')}/v2/voices",
        headers=_headers(),
        params={"category": "premade", "page_size": limit},
        timeout=30,
    )
    resp.raise_for_status()
    voices = resp.json().get("voices", [])
    return [
        {"voice_id": v["voice_id"], "name": v.get("name", ""), "description": v.get("description") or ""}
        for v in voices
        if v.get("voice_id")
    ]


def generate_voiceover(script: str, *, voice_id: str | None = None) -> bytes:
    """`script` may contain inline eleven_v3 audio tags (e.g. "[excited] ...") —
    those are sent through verbatim as part of the text, not a separate field.
    Falls back to DEFAULT_VOICE_ID if the brand has no voice_id (e.g. a brand
    created before this switch, still holding an old OpenAI preset name like
    'marin' — not a valid ElevenLabs voice_id, so it's treated the same as
    missing)."""
    settings = get_settings()
    resolved_voice_id = voice_id if voice_id and voice_id != "" else DEFAULT_VOICE_ID
    resp = httpx.post(
        f"{settings.elevenlabs_base_url}/text-to-speech/{resolved_voice_id}",
        headers={**_headers(), "Content-Type": "application/json"},
        params={"output_format": "mp3_44100_128"},
        json={
            "text": script,
            "model_id": MODEL_ID,
            "voice_settings": {"stability": STABILITY, "style": STYLE, "use_speaker_boost": True},
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content
