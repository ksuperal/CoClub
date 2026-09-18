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
    # Only return non-archived products in the library
    query = client.table("products").select("*").eq("user_id", user_id).eq("archived", False)
    if brand_id:
        query = query.eq("brand_id", brand_id)
    return query.order("created_at", desc=True).execute().data


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a single product by ID"""
    client = get_service_client()
    result = client.table("products").select("*").eq("id", product_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")
    return result.data[0]


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: str, body: ProductCreate, user_id: str = Depends(get_current_user_id)):
    """Update a product by ID"""
    client = get_service_client()

    # Check if product exists and belongs to user
    result = client.table("products").select("*").eq("id", product_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update the product (only editable fields)
    update_data = {
        "name": body.name,
        "description_text": body.description_text,
    }

    updated = client.table("products").update(update_data).eq("id", product_id).eq("user_id", user_id).execute()
    return updated.data[0]


@router.delete("/{product_id}")
def delete_product(product_id: str, user_id: str = Depends(get_current_user_id)):
    """Archive a product by ID (soft delete - removes from library but preserves for existing campaigns)"""
    from fastapi import Response

    client = get_service_client()

    # Check if product exists and belongs to user
    result = client.table("products").select("id, archived").eq("id", product_id).eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Product not found")

    if result.data[0].get("archived"):
        raise HTTPException(status_code=400, detail="Product is already archived")

    # Archive the product (soft delete) instead of hard delete
    # This keeps campaigns that reference this product working
    client.table("products").update({"archived": True}).eq("id", product_id).eq("user_id", user_id).execute()
    return Response(status_code=204)
