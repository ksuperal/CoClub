from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from ..db import get_current_user_id, get_service_client
from ..models.schemas import (
    ApproveRequest,
    CampaignCreate,
    CampaignListItem,
    CampaignOut,
    CaptionOut,
    CaptionUpdate,
    GenerateMediaRequest,
    MetricsSnapshotOut,
    PostOut,
    VariantOut,
    VariantPromptUpdate,
)
from ..pipeline.step2_variants import generate_variant_media, ideate_variants
from ..pipeline.step3_copywriting import run_copywriting
from ..pipeline.step4_approve_post import approve_campaign, post_campaign
from ..pipeline.step5_feedback import refresh_metrics as _refresh_metrics
from ..services import llm, usage
from ..services.scoring import engagement_score

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _get_owned_campaign(client: Client, campaign_id: str, user_id: str) -> dict[str, Any]:
    result = client.table("campaigns").select("*").eq("id", campaign_id).execute().data
    if not result or result[0]["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return result[0]


@router.post("", response_model=CampaignOut)
def create_campaign(body: CampaignCreate, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()

    brand = client.table("brands").select("id").eq("id", body.brand_id).eq("user_id", user_id).execute().data
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if body.product_id:
        product = (
            client.table("products")
            .select("id")
            .eq("id", body.product_id)
            .eq("user_id", user_id)
            .eq("brand_id", body.brand_id)
            .execute()
            .data
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found for this brand")

    row = (
        client.table("campaigns")
        .insert(
            {
                "brand_id": body.brand_id,
                "product_id": body.product_id,
                "user_id": user_id,
                "campaign_type": body.campaign_type,
                "brief": body.brief,
                # variant_count/media_type/audio toggles are left at their DB
                # defaults — the scoping conversation (POST .../scope/messages,
                # right after this) decides the real content_plan instead.
            }
        )
        .execute()
    )
    return row.data[0]


@router.get("", response_model=list[CampaignListItem])
def list_campaigns(user_id: str = Depends(get_current_user_id)):
    """For the home/dashboard page — every campaign the user has created, newest
    first, with the brand name and a thumbnail (first generated variant, if any)
    already attached so the frontend doesn't have to make N extra requests."""
    client = get_service_client()
    rows = (
        client.table("campaigns")
        .select("*, brands(name)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    if not rows:
        return []

    campaign_ids = [r["id"] for r in rows]
    variants = (
        client.table("variants")
        .select("campaign_id, image_url, created_at")
        .in_("campaign_id", campaign_ids)
        .order("created_at")
        .execute()
        .data
    )
    first_thumbnail_by_campaign: dict[str, str | None] = {}
    for v in variants:
        first_thumbnail_by_campaign.setdefault(v["campaign_id"], v["image_url"])

    result = []
    for row in rows:
        brand = row.pop("brands", None) or {}
        row["brand_name"] = brand.get("name")
        row["thumbnail_url"] = first_thumbnail_by_campaign.get(row["id"])
        result.append(row)
    return result


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    return _get_owned_campaign(client, campaign_id, user_id)


@router.post("/{campaign_id}/scope/messages")
def scope_message(campaign_id: str, body: dict[str, str], user_id: str = Depends(get_current_user_id)):
    """One turn of the campaign-scoping conversation — body {"text": "..."}. Before
    any ideation happens, the user describes the campaign's SIZE in their own words
    ("IG 9 posts, TikTok 2 short videos") instead of picking variant_count/media_type
    from a form; Claude either asks a follow-up or finalizes a concrete content plan.
    Campaign must be 'draft' (first call) or already 'awaiting_scope' (continuing).

    Returns {"kind": "question", "text": ...} — show it and wait for another reply —
    or {"kind": "plan", "items": [...], "summary": ...} — show `summary` and call
    /scope/confirm once the user is happy with it (or keep messaging to adjust it;
    each finalized plan overwrites the previous one, nothing commits until confirm)."""
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] not in ("draft", "awaiting_scope"):
        raise HTTPException(
            status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'draft' or 'awaiting_scope'"
        )
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="text is required")

    brand = client.table("brands").select("extracted_profile").eq("id", campaign["brand_id"]).single().execute()
    brand_profile = brand.data["extracted_profile"] or {}
    product_profile = None
    if campaign.get("product_id"):
        product = (
            client.table("products").select("extracted_profile").eq("id", campaign["product_id"]).single().execute()
        )
        product_profile = product.data["extracted_profile"] or None

    connected_platforms = [
        row["platform"]
        for row in client.table("social_accounts")
        .select("platform")
        .eq("user_id", user_id)
        .eq("status", "connected")
        .execute()
        .data
    ]

    conversation = list(campaign.get("scope_conversation") or [])
    conversation.append({"role": "user", "text": text})

    result, tokens = llm.continue_campaign_scoping(
        brand_profile=brand_profile,
        product_profile=product_profile,
        campaign_type=campaign["campaign_type"],
        brief=campaign["brief"],
        connected_platforms=connected_platforms,
        conversation=conversation,
    )
    usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=tokens)

    update: dict[str, Any] = {"status": "awaiting_scope"}
    if result["kind"] == "plan":
        conversation.append({"role": "assistant", "text": result["summary"]})
        update["content_plan"] = result["items"]
    else:
        conversation.append({"role": "assistant", "text": result["text"]})
    update["scope_conversation"] = conversation
    client.table("campaigns").update(update).eq("id", campaign_id).execute()

    return result


@router.post("/{campaign_id}/scope/confirm", response_model=list[VariantOut])
def scope_confirm(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    """Locks in the most recently finalized plan (from /scope/messages) and moves
    to ideation — writes prompts for each planned piece, no image-gen/video-gen/
    audio-gen cost yet. Campaign lands in 'awaiting_prompt_review' for the user to
    edit/skip prompts before triggering the expensive `generate-media` call."""
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "awaiting_scope":
        raise HTTPException(status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'awaiting_scope'")
    if not campaign.get("content_plan"):
        raise HTTPException(status_code=409, detail="No finalized plan yet — keep messaging /scope/messages first")
    return ideate_variants(client, user_id=user_id, campaign=campaign)


@router.patch("/{campaign_id}/variants/{variant_id}/prompt", response_model=VariantOut)
def update_variant_prompt(
    campaign_id: str, variant_id: str, body: VariantPromptUpdate, user_id: str = Depends(get_current_user_id)
):
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "awaiting_prompt_review":
        raise HTTPException(
            status_code=409,
            detail=f"Campaign is '{campaign['status']}' — prompts can only be edited before generating media",
        )

    variant = client.table("variants").select("id, campaign_id").eq("id", variant_id).execute().data
    if not variant or variant[0]["campaign_id"] != campaign_id:
        raise HTTPException(status_code=404, detail="Variant not found")

    update = {"image_prompt": body.image_prompt}
    if body.motion_prompt is not None:
        update["motion_prompt"] = body.motion_prompt
    if body.voiceover_script is not None:
        update["voiceover_script"] = body.voiceover_script
    if body.voice_instructions is not None:
        update["voice_instructions"] = body.voice_instructions
    if body.music_prompt is not None:
        update["music_prompt"] = body.music_prompt
    updated = client.table("variants").update(update).eq("id", variant_id).execute()
    return updated.data[0]


@router.post("/{campaign_id}/generate-media", response_model=list[VariantOut])
def generate_media(campaign_id: str, body: GenerateMediaRequest, user_id: str = Depends(get_current_user_id)):
    """The expensive step: generates real media only for the variants the user kept
    (possibly with edited prompts) — any other variant from this ideation round is
    deleted, never generated. Moves the campaign through 'generating_variants' to
    'awaiting_approval', the same end state `ideate`'s predecessor used to reach
    directly."""
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "awaiting_prompt_review":
        raise HTTPException(
            status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'awaiting_prompt_review'"
        )
    return generate_variant_media(client, user_id=user_id, campaign=campaign, variant_ids=body.variant_ids)


@router.get("/{campaign_id}/variants", response_model=list[VariantOut])
def list_variants(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    _get_owned_campaign(client, campaign_id, user_id)
    return client.table("variants").select("*").eq("campaign_id", campaign_id).execute().data


@router.post("/{campaign_id}/generate-copy", response_model=list[CaptionOut])
def generate_copy(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "awaiting_approval":
        raise HTTPException(
            status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'awaiting_approval'"
        )

    # Idempotency guard: a second call for the same campaign (e.g. React StrictMode's
    # double-invoked effects in dev, a retried request) must not generate a second set
    # of captions — that would silently double-post everything in Step 4. If captions
    # already exist for any variant here, return those instead of generating more.
    variant_ids = [v["id"] for v in client.table("variants").select("id").eq("campaign_id", campaign_id).execute().data]
    if variant_ids:
        existing = client.table("captions").select("*").in_("variant_id", variant_ids).execute().data
        if existing:
            return existing

    return run_copywriting(client, user_id=user_id, campaign=campaign)


@router.get("/{campaign_id}/captions", response_model=list[CaptionOut])
def list_captions(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    _get_owned_campaign(client, campaign_id, user_id)
    variant_ids = [v["id"] for v in client.table("variants").select("id").eq("campaign_id", campaign_id).execute().data]
    if not variant_ids:
        return []
    return client.table("captions").select("*").in_("variant_id", variant_ids).execute().data


@router.patch("/{campaign_id}/captions/{caption_id}", response_model=CaptionOut)
def update_caption(
    campaign_id: str, caption_id: str, body: CaptionUpdate, user_id: str = Depends(get_current_user_id)
):
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "awaiting_approval":
        raise HTTPException(
            status_code=409,
            detail=f"Campaign is '{campaign['status']}' — captions can only be edited before approving/posting",
        )

    caption = client.table("captions").select("id, variant_id").eq("id", caption_id).execute().data
    if not caption:
        raise HTTPException(status_code=404, detail="Caption not found")
    variant = client.table("variants").select("campaign_id").eq("id", caption[0]["variant_id"]).execute().data
    if not variant or variant[0]["campaign_id"] != campaign_id:
        raise HTTPException(status_code=404, detail="Caption not found")

    updated = (
        client.table("captions")
        .update({"caption_text": body.caption_text, "hashtags": body.hashtags})
        .eq("id", caption_id)
        .execute()
    )
    return updated.data[0]


@router.post("/{campaign_id}/approve")
def approve(campaign_id: str, body: ApproveRequest, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "awaiting_approval":
        raise HTTPException(
            status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'awaiting_approval'"
        )
    approve_campaign(client, campaign_id=campaign_id, approved_variant_ids=body.approved_variant_ids)
    return {"status": "approved"}


@router.post("/{campaign_id}/post", response_model=list[PostOut])
def post(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "approved":
        raise HTTPException(status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'approved'")
    return post_campaign(client, campaign_id=campaign_id, user_id=user_id)


@router.post("/{campaign_id}/metrics/refresh", response_model=list[MetricsSnapshotOut])
def refresh_campaign_metrics(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    """Fetches fresh metrics from each connected platform and stores a new snapshot
    per post. No LLM call, no status change — unlike approve/post/generate-copy this
    has no status-transition guard, since it doesn't move the pipeline forward. Safe
    to call anytime there's at least one posted post, on a `completed` campaign
    included (its posts are often still live and earning engagement)."""
    client = get_service_client()
    _get_owned_campaign(client, campaign_id, user_id)
    return _refresh_metrics(client, campaign_id)


@router.get("/{campaign_id}/metrics/history", response_model=list[MetricsSnapshotOut])
def get_campaign_metrics_history(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    """Every metrics snapshot ever fetched for this campaign's posts — the full
    history the graph renders, not just the latest point."""
    client = get_service_client()
    _get_owned_campaign(client, campaign_id, user_id)

    variant_ids = [v["id"] for v in client.table("variants").select("id").eq("campaign_id", campaign_id).execute().data]
    if not variant_ids:
        return []

    posts = client.table("posts").select("id, variant_id, platform").in_("variant_id", variant_ids).execute().data
    if not posts:
        return []
    post_by_id = {p["id"]: p for p in posts}

    metrics = client.table("post_metrics").select("*").in_("post_id", list(post_by_id.keys())).execute().data
    return [
        {
            **m,
            "variant_id": post_by_id[m["post_id"]]["variant_id"],
            "platform": post_by_id[m["post_id"]]["platform"],
            "engagement_score": engagement_score(m),
        }
        for m in metrics
    ]
