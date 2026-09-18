"""Usage logging — groundwork for future token-based billing.

Every LLM call and image-gen call writes one row here. Nothing reads/charges against
this table yet in the MVP; it exists so billing can be added later without touching
the pipeline code again.
"""

from supabase import Client


def log_usage(
    client: Client,
    *,
    user_id: str,
    campaign_id: str | None,
    kind: str,  # "llm_call" | "image_gen" | "video_gen"
    units: int,
    cost_estimate: float | None = None,
) -> None:
    client.table("usage_events").insert(
        {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "kind": kind,
            "units": units,
            "cost_estimate": cost_estimate,
        }
    ).execute()
