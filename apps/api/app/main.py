import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import assets, brands, campaigns, products, reports, social

# INFO-level logs from our own modules (e.g. pipeline/step1_intake.py's extraction
# debug logs) are silent by default since the root logger defaults to WARNING —
# this makes them show up in the same console uvicorn prints to.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="CoClub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned data API — a future second/third component gets a stable contract to code
# against (see apps/api/openapi.json, apps/api/scripts/export_openapi.py). social.router
# stays unversioned deliberately: two of its routes (/social/callback/facebook,
# /social/callback/tiktok) are OAuth redirect URIs already registered in the Meta and
# TikTok developer dashboards — versioning them would break those live integrations.
api_v1 = APIRouter(prefix="/v1")
for _router in (brands.router, products.router, campaigns.router, reports.router, assets.router):
    api_v1.include_router(_router)
app.include_router(api_v1)
app.include_router(social.router)


@app.get("/health")
def health():
    return {"status": "ok"}
