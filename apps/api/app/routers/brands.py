from fastapi import APIRouter, Depends

from ..config import get_settings
from ..db import get_current_user_id, get_service_client
from ..models.schemas import BrandCreate, BrandOut, BrandUpdate
from ..pipeline.step1_intake import run_intake
from ..services import elevenlabs_tts

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
def update_brand(brand_id: str, body: BrandUpdate, user_id: str = Depends(get_current_user_id)):
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
        "brand_voice_id": body.brand_voice_id,
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


@router.get("/voices/available")
def list_available_voices():
    """List available ElevenLabs premade voices for brand voice selection"""
    from fastapi import HTTPException

    if not get_settings().elevenlabs_enabled:
        raise HTTPException(status_code=503, detail="ElevenLabs TTS is not enabled")

    try:
        voices = elevenlabs_tts.list_premade_voices()
        return voices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {str(e)}")
