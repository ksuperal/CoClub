from fastapi import APIRouter, Depends

from ..db import get_current_user_id, get_service_client
from ..models.schemas import BrandCreate, BrandOut
from ..pipeline.step1_intake import run_intake

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=BrandOut)
def create_brand(body: BrandCreate, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    brand = run_intake(
        client,
        user_id=user_id,
        name=body.name,
        guideline_raw_text=body.guideline_raw_text,
        guideline_asset_paths=body.guideline_asset_paths,
    )
    return brand


@router.get("", response_model=list[BrandOut])
def list_brands(user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    return client.table("brands").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data
