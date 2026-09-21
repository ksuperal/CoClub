import logging
from typing import Any

from supabase import Client

from ..services import llm, usage

logger = logging.getLogger(__name__)

# YouTube removed for now — revisit once the other three platforms are validated.
PLATFORMS = ["instagram", "tiktok", "facebook"]


def run_copywriting(client: Client, *, user_id: str, campaign: dict[str, Any]) -> list[dict[str, Any]]:
    campaign_id = campaign["id"]
    brand = client.table("brands").select("extracted_profile").eq("id", campaign["brand_id"]).single().execute()
    brand_profile = brand.data["extracted_profile"] or {}

    product_profile: dict[str, Any] | None = None
    if campaign.get("product_id"):
        product = (
            client.table("products").select("extracted_profile").eq("id", campaign["product_id"]).single().execute()
        )
        product_profile = product.data["extracted_profile"] or None

    variants = client.table("variants").select("*").eq("campaign_id", campaign_id).execute().data

    all_captions: list[dict[str, Any]] = []
    failed_variants: list[str] = []

    for variant in variants:
        try:
            # target_platforms is set when this variant came from a scoped content plan
            # ("IG 9 posts" / "TikTok 2 videos" as separate, platform-specific groups) —
            # only write captions for the platform(s) it's actually meant for. Empty
            # (unscoped campaigns, or any legacy variant) means no restriction, same as
            # the old behavior of captioning for every platform.
            platforms = variant.get("target_platforms") or PLATFORMS
            captions, tokens = llm.write_captions(
                message_angle=variant["message_angle"],
                brand_profile=brand_profile,
                product_profile=product_profile,
                campaign_type=campaign["campaign_type"],
                platforms=platforms,
                product_url=campaign.get("product_url"),
                campaign_id=campaign_id,
                variant_id=variant["id"],
                structured_brief=campaign.get("structured_brief"),
            )
            usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=tokens)

            rows = [
                {
                    "variant_id": variant["id"],
                    "platform": c["platform"],
                    "caption_text": c["caption_text"],
                    "hashtags": c["hashtags"],
                }
                for c in captions
            ]
            # Upsert, not insert: if this runs twice concurrently for the same variant
            # (e.g. a StrictMode double-fired request racing another call), the
            # captions_variant_platform_unique constraint makes the second write
            # replace the first instead of creating a duplicate row.
            inserted = client.table("captions").upsert(rows, on_conflict="variant_id,platform").execute()
            all_captions.extend(inserted.data)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Failed to generate captions for variant %s in campaign %s: %s", variant["id"], campaign_id, exc
            )
            failed_variants.append(variant["id"])

    # If any variants failed, raise an error with cleanup
    if failed_variants:
        logger.error(
            "Caption generation failed for %d/%d variants in campaign %s. Rolling back all captions.",
            len(failed_variants),
            len(variants),
            campaign_id,
        )
        # Clean up partial captions
        variant_ids = [v["id"] for v in variants]
        client.table("captions").delete().in_("variant_id", variant_ids).execute()
        raise RuntimeError(
            f"Failed to generate captions for {len(failed_variants)}/{len(variants)} variants. "
            f"All captions rolled back. Variant IDs: {failed_variants}"
        )

    return all_captions
