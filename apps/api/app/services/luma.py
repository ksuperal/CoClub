"""Luma image-to-video generation (Ray model, Luma Agents API).

API reference: https://docs.agents.lumalabs.ai/. Note: this is Luma's *current*
API platform (agents.lumalabs.ai) — the older "Dream Machine" docs/domain and its
model names (ray-2, ray-flash-2, ray-1-6) are deprecated; the current (and only
valid) video model name is `ray-3.2`.

Auth is a single Bearer API key (prefixed `luma-api-`, from platform.lumalabs.ai),
sent as `Authorization: Bearer <key>` — simpler than Higgsfield's id:secret pair.
Every generation is async: submitting returns a job immediately (state "queued"),
and the caller polls `GET /v1/generations/{id}` until it reaches a terminal state
(completed/failed). This module only handles submit + poll — the actual polling
schedule lives in services/scheduler.py, which calls `check_job_status` on an
interval.

The starting image is sent inline as base64 (`video.start_frame.data`) rather than
uploaded to a hosted URL first — simpler than Higgsfield's presigned-upload flow
since Luma accepts inline image data directly. Docs call this out as intended only
for "small media files," recommending a hosted URL for anything larger; a typical
single ad-creative PNG (~1024x1024, well under a few MB) fits that, but a much
larger generated image could exceed what's reasonable to inline — flagged as a real
open risk, not fully hardened here (see TODO.md).
"""

import base64

import httpx

from ..config import get_settings

VIDEO_MODEL = "ray-3.2"


def _headers() -> dict[str, str]:
    settings = get_settings()
    return {"Authorization": f"Bearer {settings.luma_api_key}"}


def submit_image_to_video(image_bytes: bytes, motion_prompt: str, *, content_type: str = "image/png") -> str:
    """Submits an image-to-video job with the starting image inlined as base64.
    Returns Luma's generation `id` to poll via `check_job_status`. Raises on any
    failure (missing/invalid key, API error) — the caller (pipeline/step2_variants.py)
    is responsible for turning that into a variant-level generation_status='failed'
    instead of propagating a crash."""
    settings = get_settings()
    resp = httpx.post(
        f"{settings.luma_base_url}/generations",
        headers={**_headers(), "Content-Type": "application/json"},
        json={
            "model": VIDEO_MODEL,
            "type": "video",
            "prompt": motion_prompt,
            "video": {
                "resolution": "720p",
                "duration": "5s",
                "start_frame": {"data": base64.b64encode(image_bytes).decode("utf-8"), "media_type": content_type},
            },
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def check_job_status(generation_id: str) -> dict:
    """Returns the raw generation response: {id, state, output: [{type, url}], failure_reason,
    failure_code, ...}. `state` is one of queued/processing/completed/failed — only the last
    two are terminal. On `completed`, the output video URL is at `response["output"][0]["url"]`
    — that URL is presigned and expires after 1 hour, so the caller must download it promptly
    rather than storing the Luma URL directly."""
    settings = get_settings()
    resp = httpx.get(
        f"{settings.luma_base_url}/generations/{generation_id}",
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


TERMINAL_STATES = {"completed", "failed"}
