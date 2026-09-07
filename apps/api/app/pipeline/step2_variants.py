import logging
from typing import Any

from supabase import Client

from ..services import image_gen, llm, usage
from ..services.files import download_primary_asset
from .product_intake import PRODUCT_ASSETS_BUCKET

logger = logging.getLogger(__name__)

MAX_QUALITY_RETRIES = 2
VARIANTS_BUCKET = "campaign-variants"


def _upload_image(client: Client, *, user_id: str, campaign_id: str, variant_index: int, image_bytes: bytes) -> str:
    path = f"{user_id}/{campaign_id}/{variant_index}.png"
    client.storage.from_(VARIANTS_BUCKET).upload(
        path, image_bytes, {"content-type": "image/png", "upsert": "true"}
    )
    return client.storage.from_(VARIANTS_BUCKET).get_public_url(path)


def _get_product_reference_image(client: Client, campaign: dict[str, Any]) -> tuple[bytes, str] | None:
    """Fetches the product's real photo for use as an image-gen reference, if the
    campaign has a product and that product's uploaded file is a type OpenAI's edit
    endpoint accepts (PNG/JPG/WebP — not PDF/GIF)."""
    if not campaign.get("product_id"):
        return None

    product = client.table("products").select("asset_paths").eq("id", campaign["product_id"]).single().execute()
    asset_paths = product.data["asset_paths"] or []
    if not asset_paths:
        return None

    file_bytes, media_type = download_primary_asset(client, PRODUCT_ASSETS_BUCKET, asset_paths[0])
    if not file_bytes or not media_type:
        return None
    if not image_gen.supports_edit_reference(media_type):
        logger.warning(
            "Product asset media type %s isn't usable as an image-gen reference (PNG/JPG/WebP only) — "
            "falling back to text-only generation for this campaign.",
            media_type,
        )
        return None

    return file_bytes, media_type


def _generate_one_variant(
    client: Client,
    *,
    user_id: str,
    campaign_id: str,
    variant_index: int,
    angle: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None,
    product_reference: tuple[bytes, str] | None,
    campaign_type: str,
) -> dict[str, Any]:
    retry_notes: str | None = None
    attempts = 0
    passed = False
    notes = ""
    image_prompt = ""
    image_bytes = b""

    while attempts <= MAX_QUALITY_RETRIES:
        image_prompt, prompt_tokens = llm.write_image_prompt(
            angle=angle,
            brand_profile=brand_profile,
            product_profile=product_profile,
            has_reference_image=product_reference is not None,
            campaign_type=campaign_type,
            retry_notes=retry_notes,
        )
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=prompt_tokens)

        if product_reference:
            logger.info(
                "Variant %d: generating via images.edit with real product photo as reference.",
                variant_index,
            )
            image_bytes = image_gen.edit_image_with_references(image_prompt, [product_reference])
        else:
            image_bytes = image_gen.generate_image(image_prompt)
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="image_gen", units=1)

        passed, notes, check_tokens = llm.check_image_quality(
            image_bytes=image_bytes,
            media_type="image/png",
            brand_profile=brand_profile,
            product_profile=product_profile,
            reference_image=product_reference,
        )
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=check_tokens)

        attempts += 1
        if passed:
            break
        retry_notes = notes

    image_url = _upload_image(
        client, user_id=user_id, campaign_id=campaign_id, variant_index=variant_index, image_bytes=image_bytes
    )

    row = (
        client.table("variants")
        .insert(
            {
                "campaign_id": campaign_id,
                "message_angle": angle,
                "image_prompt": image_prompt,
                "image_url": image_url,
                "quality_check_status": "passed" if passed else "failed_max_retries",
                "quality_check_attempts": attempts,
                "quality_check_notes": notes,
            }
        )
        .execute()
    )
    return row.data[0]


def run_variant_generation(client: Client, *, user_id: str, campaign: dict[str, Any]) -> list[dict[str, Any]]:
    campaign_id = campaign["id"]
    brand = client.table("brands").select("extracted_profile").eq("id", campaign["brand_id"]).single().execute()
    brand_profile = brand.data["extracted_profile"] or {}

    product_profile: dict[str, Any] | None = None
    if campaign.get("product_id"):
        product = (
            client.table("products").select("extracted_profile").eq("id", campaign["product_id"]).single().execute()
        )
        product_profile = product.data["extracted_profile"] or None

    product_reference = _get_product_reference_image(client, campaign)
    logger.info(
        "Step 2 for campaign %s: product_id=%s, image mode=%s",
        campaign_id,
        campaign.get("product_id"),
        "reference photo (images.edit)" if product_reference else "text-only (images.generate)",
    )

    client.table("campaigns").update({"status": "generating_variants"}).eq("id", campaign_id).execute()

    try:
        angles, ideation_tokens = llm.ideate_message_angles(
            brand_profile=brand_profile,
            product_profile=product_profile,
            campaign_type=campaign["campaign_type"],
            brief=campaign["brief"],
            n=campaign["variant_count"],
        )
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=ideation_tokens)

        variants = [
            _generate_one_variant(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                variant_index=i,
                angle=angle,
                brand_profile=brand_profile,
                product_profile=product_profile,
                product_reference=product_reference,
                campaign_type=campaign["campaign_type"],
            )
            for i, angle in enumerate(angles)
        ]

        client.table("campaigns").update({"status": "awaiting_approval"}).eq("id", campaign_id).execute()
        return variants
    except Exception as exc:  # noqa: BLE001
        client.table("campaigns").update(
            {"status": "failed", "error_message": f"Step 2 (variant generation) failed: {exc}"}
        ).eq("id", campaign_id).execute()
        raise
