import uuid

from fastapi import APIRouter, Depends, UploadFile

from ..db import get_current_user_id, get_service_client

router = APIRouter(prefix="/assets", tags=["assets"])


async def _upload(bucket: str, file: UploadFile, user_id: str) -> dict[str, str]:
    client = get_service_client()
    contents = await file.read()
    ext = (file.filename or "").rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
    path = f"{user_id}/{uuid.uuid4()}.{ext}"

    client.storage.from_(bucket).upload(
        path, contents, {"content-type": file.content_type or "application/octet-stream"}
    )
    return {"path": path}


@router.post("/brand-guideline")
async def upload_brand_asset(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    """Uploads one brand asset file, returns its storage path for use in
    POST /brands { guideline_asset_paths: [...] }."""
    return await _upload("brand-assets", file, user_id)


@router.post("/product")
async def upload_product_asset(file: UploadFile, user_id: str = Depends(get_current_user_id)):
    """Uploads one product photo/file, returns its storage path for use in
    POST /products { asset_paths: [...] }."""
    return await _upload("product-assets", file, user_id)
