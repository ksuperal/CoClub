"""OpenAI text-to-speech (gpt-4o-mini-tts) — voiceover for video variants.

Reuses the same OpenAI account/key already required for gpt-image-2 (see
services/image_gen.py) — no new vendor account needed, unlike Luma or ElevenLabs.
gpt-4o-mini-tts is current-generation, steerable (a plain-language `instructions`
string controls tone/pace/emotion, not just which of the 13 preset voices is
used) and priced per token (~$0.015/minute of output audio) rather than the
older tts-1/tts-1-hd's flat per-character rate — cheaper and better quality, not
a tradeoff between the two.
"""

from openai import OpenAI

from ..config import get_settings

TTS_MODEL = "gpt-4o-mini-tts"

# The 13 voices gpt-4o-mini-tts currently supports. OpenAI recommends `marin` or
# `cedar` when output quality is the priority — used as the fallback default for
# brands created before voice selection existed, or if that LLM call ever fails.
VALID_VOICES = [
    "alloy", "ash", "ballad", "coral", "echo", "fable",
    "nova", "onyx", "sage", "shimmer", "verse", "marin", "cedar",
]
DEFAULT_VOICE = "marin"


def _client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)


def generate_voiceover(script: str, *, voice: str | None = None, instructions: str | None = None) -> bytes:
    """Synchronous call — returns raw MP3 bytes directly, no job/poll pattern
    (unlike Luma video). `voice` should be one of VALID_VOICES; falls back to
    DEFAULT_VOICE if not recognized rather than letting an invalid brand.voice_id
    (e.g. from data written before this list existed) fail the whole request."""
    resolved_voice = voice if voice in VALID_VOICES else DEFAULT_VOICE
    resp = _client().audio.speech.create(
        model=TTS_MODEL,
        voice=resolved_voice,
        input=script,
        instructions=instructions or "",
        response_format="mp3",
    )
    return resp.read()
