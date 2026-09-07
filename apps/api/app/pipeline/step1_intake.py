import json
import logging
from typing import Any

from supabase import Client

from ..services import llm, usage
from ..services.files import download_assets_with_paths

logger = logging.getLogger(__name__)

BRAND_ASSETS_BUCKET = "brand-assets"


def run_intake(
    client: Client, *, user_id: str, name: str, guideline_raw_text: str, guideline_asset_paths: list[str]
) -> dict[str, Any]:
    """Structured extraction of the brand profile, then persists the brand row.

    Every uploaded guideline file that Claude can read (image or PDF, any count) is
    sent as the primary source; pasted guideline text is supplementary. See
    llm.extract_brand_profile.
    """
    downloaded = download_assets_with_paths(client, BRAND_ASSETS_BUCKET, guideline_asset_paths)
    files = [(file_bytes, media_type) for _, file_bytes, media_type in downloaded]

    logger.info(
        "Step 1 intake for brand '%s': %d/%d uploaded file(s) usable, pasted_text_len=%d",
        name,
        len(files),
        len(guideline_asset_paths),
        len(guideline_raw_text or ""),
    )

    profile, output_tokens = llm.extract_brand_profile(guideline_raw_text, files=files)

    # Claude reports logo/mascot findings by file_index (position in `files` above) —
    # we persist which real storage path that index maps to ourselves, deterministically,
    # rather than relying on Claude to echo the path back (which risks hallucination).
    profile["source_files"] = [path for path, _, _ in downloaded]

    logger.info("Step 1 extracted brand profile for '%s':\n%s", name, json.dumps(profile, indent=2))

    row = (
        client.table("brands")
        .insert(
            {
                "user_id": user_id,
                "name": name,
                "guideline_raw_text": guideline_raw_text,
                "guideline_assets": guideline_asset_paths,
                "extracted_profile": profile,
            }
        )
        .execute()
    )
    brand = row.data[0]

    usage.log_usage(
        client, user_id=user_id, campaign_id=None, kind="llm_call", units=output_tokens
    )

    return brand
