"""Step 5: 24hrs after posting, fetch metrics, compute stats in code, and have the
LLM narrate the pre-computed verdicts (it never invents numbers itself).

Invoked by the APScheduler job registered in services/scheduler.py — runs with no
HTTP request context, so it builds its own service-role client.
"""

from typing import Any

from ..db import get_service_client
from ..services import llm, social, usage


def _engagement_score(m: dict[str, Any]) -> int:
    return m["likes"] + 2 * m["comments"] + 3 * m["shares"] + m["views"] // 10


def run_feedback_job(campaign_id: str) -> None:
    client = get_service_client()

    campaign = client.table("campaigns").select("*").eq("id", campaign_id).single().execute().data
    variants = client.table("variants").select("*").eq("campaign_id", campaign_id).eq("status", "approved").execute().data

    verdicts: list[dict[str, Any]] = []

    for variant in variants:
        posts = client.table("posts").select("*").eq("variant_id", variant["id"]).execute().data
        variant_score = 0
        platform_breakdown: list[dict[str, Any]] = []
        has_real_data = False

        for post in posts:
            if post["status"] == "posted" and post["external_post_id"]:
                has_real_data = True
                metrics = social.fetch_metrics(post["external_post_id"])
                client.table("post_metrics").insert({"post_id": post["id"], **metrics}).execute()
                score = _engagement_score(metrics)
                variant_score += score
                platform_breakdown.append({"platform": post["platform"], **metrics, "score": score})
            else:
                platform_breakdown.append({"platform": post["platform"], "status": post["status"]})

        verdicts.append(
            {
                "variant_id": variant["id"],
                "message_angle": variant["message_angle"],
                "has_real_data": has_real_data,
                "total_engagement_score": variant_score,
                "platform_breakdown": platform_breakdown,
            }
        )

    verdicts.sort(key=lambda v: v["total_engagement_score"], reverse=True)
    top_variant_id = verdicts[0]["variant_id"] if verdicts and verdicts[0]["has_real_data"] else None

    if not verdicts or not any(v["has_real_data"] for v in verdicts):
        summary_text = (
            "No live post data is available yet for this campaign — posting hasn't been "
            "connected (Ayrshare credentials aren't configured), so there's nothing to report "
            "on. Add AYRSHARE_API_KEY and re-run posting to get real performance data."
        )
        output_tokens = 0
    else:
        summary_text, output_tokens = llm.narrate_report(
            campaign_type=campaign["campaign_type"], verdicts=verdicts
        )

    client.table("campaign_reports").insert(
        {
            "campaign_id": campaign_id,
            "summary_text": summary_text,
            "top_variant_id": top_variant_id,
            "verdicts": verdicts,
        }
    ).execute()

    if output_tokens:
        usage.log_usage(
            client, user_id=campaign["user_id"], campaign_id=campaign_id, kind="llm_call", units=output_tokens
        )

    client.table("campaigns").update({"status": "completed"}).eq("id", campaign_id).execute()
