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
    PostOut,
    VariantOut,
)
from ..pipeline.step2_variants import run_variant_generation
from ..pipeline.step3_copywriting import run_copywriting
from ..pipeline.step4_approve_post import approve_campaign, post_campaign

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
                "variant_count": body.variant_count,
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


@router.post("/{campaign_id}/generate-variants", response_model=list[VariantOut])
def generate_variants(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    campaign = _get_owned_campaign(client, campaign_id, user_id)
    if campaign["status"] != "draft":
        raise HTTPException(status_code=409, detail=f"Campaign is '{campaign['status']}', expected 'draft'")
    return run_variant_generation(client, user_id=user_id, campaign=campaign)


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
    return run_copywriting(client, user_id=user_id, campaign=campaign)


@router.get("/{campaign_id}/captions", response_model=list[CaptionOut])
def list_captions(campaign_id: str, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    _get_owned_campaign(client, campaign_id, user_id)
    variant_ids = [v["id"] for v in client.table("variants").select("id").eq("campaign_id", campaign_id).execute().data]
    if not variant_ids:
        return []
    return client.table("captions").select("*").in_("variant_id", variant_ids).execute().data


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
