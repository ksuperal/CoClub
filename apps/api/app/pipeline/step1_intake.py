import json
import logging
from typing import Any

from supabase import Client

from ..services import llm, usage
from ..services.files import download_primary_asset

logger = logging.getLogger(__name__)

BRAND_ASSETS_BUCKET = "brand-assets"


def run_intake(
    client: Client, *, user_id: str, name: str, guideline_raw_text: str, guideline_asset_paths: list[str]
) -> dict[str, Any]:
    """Structured extraction of the brand profile, then persists the brand row.

    Prioritizes the uploaded guideline file (if any) as the primary source; pasted
    guideline text is sent as supplementary context. See llm.extract_brand_profile.
    """
    file_bytes: bytes | None = None
    file_media_type: str | None = None
    if guideline_asset_paths:
        file_bytes, file_media_type = download_primary_asset(client, BRAND_ASSETS_BUCKET, guideline_asset_paths[0])

    logger.info(
        "Step 1 intake for brand '%s': source=%s, pasted_text_len=%d, uploaded_asset_paths=%s",
        name,
        f"uploaded file ({file_media_type})" if file_bytes else "pasted text only",
        len(guideline_raw_text or ""),
        guideline_asset_paths,
    )

    profile, output_tokens = llm.extract_brand_profile(
        guideline_raw_text, file_bytes=file_bytes, file_media_type=file_media_type
    )

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
