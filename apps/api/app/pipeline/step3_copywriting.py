from typing import Any

from supabase import Client

from ..services import llm, usage

PLATFORMS = ["instagram", "tiktok", "youtube", "facebook"]


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
    for variant in variants:
        captions, tokens = llm.write_captions(
            message_angle=variant["message_angle"],
            brand_profile=brand_profile,
            product_profile=product_profile,
            campaign_type=campaign["campaign_type"],
            platforms=PLATFORMS,
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
        inserted = client.table("captions").insert(rows).execute()
        all_captions.extend(inserted.data)

    return all_captions
