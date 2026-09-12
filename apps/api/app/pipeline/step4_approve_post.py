from datetime import datetime, timezone
from typing import Any

from supabase import Client

from ..services import social
from ..services.scheduler import schedule_feedback_job, schedule_metrics_polling


def approve_campaign(client: Client, *, campaign_id: str, approved_variant_ids: list[str]) -> None:
    variants = client.table("variants").select("id").eq("campaign_id", campaign_id).execute().data
    for v in variants:
        status = "approved" if v["id"] in approved_variant_ids else "rejected"
        client.table("variants").update({"status": status}).eq("id", v["id"]).execute()

    client.table("campaigns").update({"status": "approved"}).eq("id", campaign_id).execute()


def post_campaign(client: Client, *, campaign_id: str, user_id: str) -> list[dict[str, Any]]:
    client.table("campaigns").update({"status": "posting"}).eq("id", campaign_id).execute()

    approved_variants = (
        client.table("variants")
        .select("*")
        .eq("campaign_id", campaign_id)
        .eq("status", "approved")
        .execute()
        .data
    )

    created_posts: list[dict[str, Any]] = []
    try:
        for variant in approved_variants:
            captions = client.table("captions").select("*").eq("variant_id", variant["id"]).execute().data
            for caption in captions:
                result = social.post_to_platform(
                    client,
                    user_id=user_id,
                    platform=caption["platform"],
                    caption_text=caption["caption_text"],
                    hashtags=caption["hashtags"],
                    image_url=variant["image_url"],
                )
                row = (
                    client.table("posts")
                    .insert(
                        {
                            "variant_id": variant["id"],
                            "platform": caption["platform"],
                            "status": result.status,
                            "external_post_id": result.external_post_id,
                            "permalink": result.permalink,
                            "error_message": result.error_message,
                            # Only set once a post actually landed — used to plot the
                            # metrics graph against real time and to bucket posts by
                            # hour for the posting-time recommendation.
                            "posted_at": datetime.now(timezone.utc).isoformat() if result.status == "posted" else None,
                        }
                    )
                    .execute()
                )
                created_posts.append(row.data[0])

        client.table("campaigns").update({"status": "posted"}).eq("id", campaign_id).execute()
        schedule_feedback_job(campaign_id)
        # Only worth polling if something actually landed — a campaign where every
        # post came back pending_credentials/failed has nothing for refresh_metrics
        # to find every 6 hours.
        if any(p["status"] == "posted" for p in created_posts):
            schedule_metrics_polling(campaign_id)
        client.table("campaigns").update({"status": "awaiting_feedback"}).eq("id", campaign_id).execute()
        return created_posts
    except Exception as exc:  # noqa: BLE001
        client.table("campaigns").update(
            {"status": "failed", "error_message": f"Step 4 (posting) failed: {exc}"}
        ).eq("id", campaign_id).execute()
        raise
