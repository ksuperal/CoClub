from fastapi import APIRouter, Depends

from ..db import get_current_user_id, get_service_client
from ..models.schemas import BrandCreate, BrandOut
from ..pipeline.step1_intake import run_intake

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("", response_model=BrandOut)
def create_brand(body: BrandCreate, user_id: str = Depends(get_current_user_id)):
    from fastapi import HTTPException

    client = get_service_client()

    # Check if a brand with the same name already exists for this user (excluding archived)
    existing = client.table("brands").select("id").eq("user_id", user_id).eq("archived", False).ilike("name", body.name).execute()
    if existing.data:
        raise HTTPException(
            status_code=400,
            detail=f"A brand named '{body.name}' already exists. Please choose a different name."
        )

    brand = run_intake(
        client,
        user_id=user_id,
        name=body.name,
        guideline_raw_text=body.guideline_raw_text,
        guideline_asset_paths=body.guideline_asset_paths,
        description=body.description,
    )
    return brand


@router.get("", response_model=list[BrandOut])
def list_brands(user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    # Only return non-archived brands in the library
    return client.table("brands").select("*").eq("user_id", user_id).eq("archived", False).order("created_at", desc=True).execute().data


@router.get("/{brand_id}", response_model=BrandOut)
def get_brand(brand_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a single brand by ID"""
    from fastapi import HTTPException

    client = get_service_client()
    result = client.table("brands").select("*").eq("id", brand_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Brand not found")
    return result.data[0]


@router.patch("/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: str, body: BrandCreate, user_id: str = Depends(get_current_user_id)):
    """Update a brand by ID"""
    from fastapi import HTTPException

    client = get_service_client()

    # Check if brand exists and belongs to user
    result = client.table("brands").select("*").eq("id", brand_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Check if name is being changed to a duplicate (excluding archived brands)
    if body.name.lower() != result.data[0]["name"].lower():
        existing = client.table("brands").select("id").eq("user_id", user_id).eq("archived", False).ilike("name", body.name).execute()
        if existing.data:
            raise HTTPException(
                status_code=400,
                detail=f"A brand named '{body.name}' already exists. Please choose a different name."
            )

    # Update the brand (only editable fields)
    update_data = {
        "name": body.name,
        "description": body.description,
    }

    updated = client.table("brands").update(update_data).eq("id", brand_id).eq("user_id", user_id).execute()
    return updated.data[0]


@router.delete("/{brand_id}")
def delete_brand(brand_id: str, user_id: str = Depends(get_current_user_id)):
    """Archive a brand by ID (soft delete - removes from library but preserves for existing campaigns)"""
    from fastapi import HTTPException, Response

    client = get_service_client()

    # Check if brand exists and belongs to user
    result = client.table("brands").select("id, archived").eq("id", brand_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Brand not found")

    if result.data[0].get("archived"):
        raise HTTPException(status_code=400, detail="Brand is already archived")

    # Archive the brand (soft delete) instead of hard delete
    # This keeps campaigns that reference this brand working
    client.table("brands").update({"archived": True}).eq("id", brand_id).eq("user_id", user_id).execute()
    return Response(status_code=204)
