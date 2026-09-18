"""Shared helpers for pulling uploaded files back out of storage — used by brand
intake, product intake, and Step 2's image-gen reference gathering, so "download it,
check what it is, log what happened" is one piece of logic, not three."""

import logging
import mimetypes

from supabase import Client

logger = logging.getLogger(__name__)

# Claude can read these directly (image content block or PDF document block) for
# text extraction. Anything else is skipped, with a warning logged.
CLAUDE_READABLE_MEDIA_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp", "image/gif"}


def download_asset(client: Client, bucket: str, path: str) -> tuple[bytes | None, str | None]:
    """Downloads one uploaded file. Returns (None, None) if its type isn't one Claude
    can read directly (extraction) — callers that need OpenAI's narrower image-gen
    type set filter further themselves."""
    media_type, _ = mimetypes.guess_type(path)
    if media_type not in CLAUDE_READABLE_MEDIA_TYPES:
        logger.warning(
            "Asset '%s' in bucket '%s' has unsupported/unrecognized media type %s.", path, bucket, media_type
        )
        return None, None

    try:
        file_bytes = client.storage.from_(bucket).download(path)
    except Exception:
        logger.exception("Failed to download asset '%s' from bucket '%s'.", path, bucket)
        return None, None

    logger.info("Downloaded asset '%s' from '%s' (%s, %d bytes).", path, bucket, media_type, len(file_bytes))
    return file_bytes, media_type


def download_assets(client: Client, bucket: str, paths: list[str]) -> list[tuple[bytes, str]]:
    """Downloads every path that's a Claude-readable type, in order, skipping (with a
    warning already logged by download_asset) anything else."""
    results: list[tuple[bytes, str]] = []
    for path in paths or []:
        file_bytes, media_type = download_asset(client, bucket, path)
        if file_bytes and media_type:
            results.append((file_bytes, media_type))
    return results


def download_assets_with_paths(client: Client, bucket: str, paths: list[str]) -> list[tuple[str, bytes, str]]:
    """Like download_assets, but keeps each file's storage path alongside its bytes —
    needed when a downstream step must map back to which uploaded file is which (e.g.
    targeting a specific page within a specific PDF that Claude identified as showing
    the brand's logo/mascot)."""
    results: list[tuple[str, bytes, str]] = []
    for path in paths or []:
        file_bytes, media_type = download_asset(client, bucket, path)
        if file_bytes and media_type:
            results.append((path, file_bytes, media_type))
    return results


def rasterize_pdf_pages(
    pdf_bytes: bytes, *, page_numbers: list[int] | None = None, max_pages: int = 2, dpi: int = 150
) -> list[tuple[bytes, str]]:
    """Renders PDF pages into PNG images. OpenAI's image-gen edit endpoint doesn't
    accept PDFs directly (only Claude's text extraction does) — this is how a PDF
    brand guideline or product spec sheet still becomes usable as a real visual
    reference for image generation.

    If `page_numbers` (1-indexed) is given, renders exactly those pages (used when
    Claude already identified which page shows something worth using, e.g. a logo).
    Otherwise renders the first `max_pages` pages (blind fallback)."""
    import fitz  # PyMuPDF — imported lazily, only needed when a PDF is actually uploaded

    images: list[tuple[bytes, str]] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        zoom = dpi / 72  # PDF units are 72 points per inch
        matrix = fitz.Matrix(zoom, zoom)
        if page_numbers is not None:
            indices = [n - 1 for n in page_numbers if 1 <= n <= doc.page_count]
        else:
            indices = list(range(min(max_pages, doc.page_count)))
        for index in indices:
            pixmap = doc[index].get_pixmap(matrix=matrix)
            images.append((pixmap.tobytes("png"), "image/png"))
    finally:
        doc.close()
    return images
