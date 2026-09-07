"""Shared helper for pulling an uploaded file back out of storage so it can be sent
to Claude as a primary extraction source (brand intake and product intake both use
this — same "download it, check Claude can read it" logic either way)."""

import logging
import mimetypes

from supabase import Client

logger = logging.getLogger(__name__)

# Claude can read these directly (image content block or PDF document block).
# Anything else falls back to text-only extraction, with a warning logged.
SUPPORTED_MEDIA_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp", "image/gif"}


def download_primary_asset(client: Client, bucket: str, path: str) -> tuple[bytes | None, str | None]:
    """Downloads one uploaded file to use as a primary LLM extraction source.
    Returns (None, None) if the file type isn't one Claude can read directly."""
    media_type, _ = mimetypes.guess_type(path)
    if media_type not in SUPPORTED_MEDIA_TYPES:
        logger.warning(
            "Asset '%s' in bucket '%s' has unsupported/unrecognized media type %s — Claude can't read "
            "it directly.",
            path,
            bucket,
            media_type,
        )
        return None, None

    try:
        file_bytes = client.storage.from_(bucket).download(path)
    except Exception:
        logger.exception("Failed to download asset '%s' from bucket '%s'.", path, bucket)
        return None, None

    logger.info("Downloaded asset '%s' from '%s' (%s, %d bytes).", path, bucket, media_type, len(file_bytes))
    return file_bytes, media_type
