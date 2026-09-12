"""Step 5: fetch live metrics, compute stats in code, and (only when explicitly
asked — the 24hr scheduler or a manual "run report now") have the LLM narrate the
pre-computed verdicts (it never invents numbers itself).

`refresh_metrics` is the cheap, LLM-free half: fetch real numbers from the platform,
store a new snapshot, return them. Safe to call as often as wanted — it's what backs
the metrics graph. `run_feedback_job` builds on top of it for the full LLM report,
invoked by the APScheduler job registered in services/scheduler.py (no HTTP request
context, so it builds its own service-role client) or via the manual "run now" route.
"""

import logging
from typing import Any

from ..db import get_service_client
from ..services import llm, social, usage
from ..services.scoring import engagement_score

logger = logging.getLogger(__name__)


def refresh_metrics(client, campaign_id: str) -> list[dict[str, Any]]:
    """Fetches fresh metrics for every posted post of this campaign's approved
    variants, inserts a new `post_metrics` snapshot per post (history accumulates —
    each call adds a row, nothing is overwritten), and returns what it fetched. No
    LLM call, no `campaign_reports` row, no `campaigns.status` change — this is the
    part that's fine to call anytime, repeatedly, independent of the pipeline's
    overall status.
    """
    campaign = client.table("campaigns").select("user_id").eq("id", campaign_id).single().execute().data
    variants = (
        client.table("variants").select("id").eq("campaign_id", campaign_id).eq("status", "approved").execute().data
    )

    fetched: list[dict[str, Any]] = []
    for variant in variants:
        posts = client.table("posts").select("*").eq("variant_id", variant["id"]).execute().data
        for post in posts:
            if post["status"] != "posted" or not post["external_post_id"]:
                continue
            metrics = social.fetch_metrics(
                client, user_id=campaign["user_id"], platform=post["platform"], external_post_id=post["external_post_id"]
            )
            if metrics is None:
                # The call itself failed (rate limit, network, transient API error) —
                # not the same as zero engagement. Skip writing a snapshot rather than
                # recording a false zero; the next scheduled poll tries again.
                continue
            row = client.table("post_metrics").insert({"post_id": post["id"], **metrics}).execute().data[0]
            fetched.append(
                {
                    "post_id": post["id"],
                    "platform": post["platform"],
                    "variant_id": variant["id"],
                    "engagement_score": engagement_score(row),
                    **row,
                }
            )

    return fetched


def run_scheduled_metrics_refresh(campaign_id: str) -> None:
    """Entry point for the recurring background poll (services/scheduler.py,
    schedule_metrics_polling) — same no-HTTP-context situation as run_feedback_job,
    builds its own client. Logs and swallows errors so one bad tick (a token expired,
    a platform API hiccup) doesn't take down the scheduler or spam retries — the
    next tick a few hours later just tries again."""
    try:
        client = get_service_client()
        refresh_metrics(client, campaign_id)
    except Exception:  # noqa: BLE001
        logger.exception("Scheduled metrics refresh failed for campaign %s", campaign_id)


def run_feedback_job(campaign_id: str) -> None:
    client = get_service_client()

    campaign = client.table("campaigns").select("*").eq("id", campaign_id).single().execute().data
    variants = client.table("variants").select("*").eq("campaign_id", campaign_id).eq("status", "approved").execute().data

    fresh_metrics = refresh_metrics(client, campaign_id)
    metrics_by_post_id = {m["post_id"]: m for m in fresh_metrics}

    verdicts: list[dict[str, Any]] = []

    for variant in variants:
        posts = client.table("posts").select("*").eq("variant_id", variant["id"]).execute().data
        variant_score = 0
        platform_breakdown: list[dict[str, Any]] = []
        has_real_data = False

        for post in posts:
            metrics = metrics_by_post_id.get(post["id"])
            if post["status"] == "posted" and post["external_post_id"] and metrics:
                has_real_data = True
                score = engagement_score(metrics)
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
            "No live post data is available yet for this campaign — no connected social "
            "accounts were available to post to, so there's nothing to report on. Connect "
            "your accounts under Settings and re-run posting to get real performance data."
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
