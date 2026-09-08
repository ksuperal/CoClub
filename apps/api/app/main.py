import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import assets, brands, campaigns, products, reports, social

# INFO-level logs from our own modules (e.g. pipeline/step1_intake.py's extraction
# debug logs) are silent by default since the root logger defaults to WARNING —
# this makes them show up in the same console uvicorn prints to.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="CoClub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(brands.router)
app.include_router(products.router)
app.include_router(campaigns.router)
app.include_router(reports.router)
app.include_router(assets.router)
app.include_router(social.router)


@app.get("/health")
def health():
    return {"status": "ok"}
