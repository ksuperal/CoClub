from fastapi import APIRouter, Depends, HTTPException

from ..db import get_current_user_id, get_service_client
from ..models.schemas import ProductCreate, ProductOut
from ..pipeline.product_intake import run_product_intake

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut)
def create_product(body: ProductCreate, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()

    brand = client.table("brands").select("id").eq("id", body.brand_id).eq("user_id", user_id).execute().data
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    try:
        return run_product_intake(
            client,
            user_id=user_id,
            brand_id=body.brand_id,
            name=body.name,
            description_text=body.description_text,
            asset_paths=body.asset_paths,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[ProductOut])
def list_products(brand_id: str | None = None, user_id: str = Depends(get_current_user_id)):
    client = get_service_client()
    query = client.table("products").select("*").eq("user_id", user_id)
    if brand_id:
        query = query.eq("brand_id", brand_id)
    return query.order("created_at", desc=True).execute().data
