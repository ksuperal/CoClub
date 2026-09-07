from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

CampaignType = Literal[
    "product_launch", "event_announcement", "promo_offer", "brand_awareness", "other"
]
Platform = Literal["instagram", "tiktok", "facebook"]  # youtube removed for now


# ---------------------------------------------------------------------------
# Brands (Step 1)
# ---------------------------------------------------------------------------
class BrandCreate(BaseModel):
    name: str
    guideline_raw_text: str = Field(
        ..., description="Pasted/extracted text of the brand guideline"
    )
    guideline_asset_paths: list[str] = Field(
        default_factory=list, description="Paths already uploaded to the brand-assets bucket"
    )


class BrandOut(BaseModel):
    id: str
    name: str
    extracted_profile: dict[str, Any] | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Products — file upload is required (the primary source), text is optional
# ---------------------------------------------------------------------------
class ProductCreate(BaseModel):
    brand_id: str
    name: str
    description_text: str | None = Field(
        default=None, description="Optional supplementary text — the upload is the primary source"
    )
    asset_paths: list[str] = Field(
        ..., min_length=1, description="Required — at least one path uploaded to the product-assets bucket"
    )


class ProductOut(BaseModel):
    id: str
    brand_id: str
    name: str
    description_text: str | None
    extracted_profile: dict[str, Any] | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------
class CampaignCreate(BaseModel):
    brand_id: str
    product_id: str | None = Field(default=None, description="Optional — ties this campaign to a specific product")
    campaign_type: CampaignType
    brief: str
    variant_count: int = Field(default=4, ge=1, le=10)


class CampaignOut(BaseModel):
    id: str
    brand_id: str
    product_id: str | None
    campaign_type: str
    brief: str
    variant_count: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class CampaignListItem(BaseModel):
    """For the home/dashboard page — a campaign plus enough denormalized context
    (brand name, a thumbnail) to render a list without extra requests per row."""

    id: str
    brand_id: str
    brand_name: str | None
    product_id: str | None
    campaign_type: str
    brief: str
    status: str
    thumbnail_url: str | None
    created_at: datetime


class VariantOut(BaseModel):
    id: str
    message_angle: str
    image_prompt: str
    image_url: str | None
    quality_check_status: str
    quality_check_attempts: int
    status: str


class CaptionOut(BaseModel):
    id: str
    variant_id: str
    platform: str
    caption_text: str
    hashtags: list[str]


class ApproveRequest(BaseModel):
    approved_variant_ids: list[str]


class PostOut(BaseModel):
    id: str
    variant_id: str
    platform: str
    status: str
    permalink: str | None
    error_message: str | None


class CampaignReportOut(BaseModel):
    id: str
    campaign_id: str
    summary_text: str
    top_variant_id: str | None
    verdicts: list[dict[str, Any]]
    created_at: datetime
