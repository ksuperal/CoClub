"""OpenAI Images API wrapper (gpt-image-2)."""

import base64

from openai import OpenAI

from ..config import get_settings


def _client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)


def generate_image(prompt: str, *, size: str = "1024x1024") -> bytes:
    """Text-only generation — no reference image available. Returns raw PNG bytes."""
    settings = get_settings()
    resp = _client().images.generate(
        model=settings.openai_image_model,
        prompt=prompt,
        size=size,
        n=1,
    )
    b64 = resp.data[0].b64_json
    return base64.b64decode(b64)


# Media types the edit endpoint accepts as reference images (per OpenAI's docs — GIF/PDF
# are not supported here even though Claude can read them for extraction elsewhere).
_EDIT_EXTENSIONS = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}


def supports_edit_reference(media_type: str) -> bool:
    return media_type in _EDIT_EXTENSIONS


def edit_image_with_references(
    prompt: str, reference_images: list[tuple[bytes, str]], *, size: str = "1024x1024"
) -> bytes:
    """Generates an image using OpenAI's edit endpoint with real reference photo(s) as
    input, so the output is grounded in actual pixels instead of a text-only guess.
    `reference_images` is a list of (raw_bytes, media_type) — used when a campaign's
    product has an uploaded photo. Returns raw PNG bytes."""
    settings = get_settings()
    files = [
        (f"reference_{i}.{_EDIT_EXTENSIONS[media_type]}", data, media_type)
        for i, (data, media_type) in enumerate(reference_images)
    ]
    resp = _client().images.edit(
        model=settings.openai_image_model,
        image=files,
        prompt=prompt,
        size=size,
        n=1,
    )
    b64 = resp.data[0].b64_json
    return base64.b64decode(b64)
