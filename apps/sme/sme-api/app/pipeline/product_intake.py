import json
import logging
from typing import Any

from supabase import Client

from ..services import llm, usage
from ..services.files import download_assets

logger = logging.getLogger(__name__)

PRODUCT_ASSETS_BUCKET = "product-assets"


def run_product_intake(
    client: Client,
    *,
    user_id: str,
    brand_id: str,
    name: str,
    description_text: str | None,
    asset_paths: list[str],
) -> dict[str, Any]:
    """Structured extraction of the product profile, then persists the product row.

    The upload is required (the router checks `asset_paths` is non-empty before this
    is called) — every uploaded file that Claude can read (image or PDF, any count) is
    the primary source, the text description is supplementary, same priority rule as
    brand intake. Raises ValueError if none of the uploaded files are a type Claude
    can read directly.
    """
    files = download_assets(client, PRODUCT_ASSETS_BUCKET, asset_paths)
    if not files:
        raise ValueError(
            "None of the uploaded product file(s) could be read as an image or PDF — please upload "
            "PNG/JPG/WEBP/GIF or PDF."
        )

    logger.info(
        "Product intake for '%s': %d/%d uploaded file(s) usable, description_text_len=%d",
        name,
        len(files),
        len(asset_paths),
        len(description_text or ""),
    )

    profile, output_tokens = llm.extract_product_profile(description_text, files=files)

    logger.info("Extracted product profile for '%s':\n%s", name, json.dumps(profile, indent=2))

    row = (
        client.table("products")
        .insert(
            {
                "user_id": user_id,
                "brand_id": brand_id,
                "name": name,
                "description_text": description_text,
                "asset_paths": asset_paths,
                "extracted_profile": profile,
            }
        )
        .execute()
    )
    product = row.data[0]

    usage.log_usage(client, user_id=user_id, campaign_id=None, kind="llm_call", units=output_tokens)

    return product
