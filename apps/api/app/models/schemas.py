from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

CampaignType = Literal[
    "product_launch", "event_announcement", "promo_offer", "brand_awareness", "other"
]
Platform = Literal["instagram", "tiktok", "facebook"]  # youtube removed for now
MediaType = Literal["image", "video"]
GenerationStatus = Literal["awaiting_prompt_review", "generating", "generated", "failed"]


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
    voice_id: str | None = None  # defaults until the 0007 migration is applied
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
        ...,
        min_length=1,
        max_length=10,
        description="Required — 1 to 10 paths uploaded to the product-assets bucket"
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
    # No variant_count/media_type/audio toggles here anymore — the campaign-scoping
    # conversation (POST /campaigns/{id}/scope/messages, right after creation) decides
    # those, letting the user describe size in their own words ("IG 9 posts, TikTok 2
    # short videos") instead of picking mechanical settings before seeing anything.


class CampaignOut(BaseModel):
    id: str
    brand_id: str
    product_id: str | None
    campaign_type: str
    brief: str
    variant_count: int  # legacy fallback default — see step2_variants._expand_content_plan
    media_type: str = "image"  # legacy fallback default — content_plan is authoritative once scoping finishes
    include_voiceover: bool = False
    include_music: bool = False
    scope_conversation: list[dict[str, Any]] = Field(default_factory=list)
    content_plan: list[dict[str, Any]] | None = None
    status: str
    error_message: str | None
    warning_message: str | None = None  # defaults to None until the 0005 migration is applied
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
    media_type: str = "image"  # defaults until the 0006 migration is applied
    motion_prompt: str | None = None
    video_url: str | None = None
    generation_status: str = "generated"
    video_gen_error: str | None = None
    voiceover_script: str | None = None  # defaults until the 0007 migration is applied
    voice_instructions: str | None = None
    music_prompt: str | None = None
    audio_gen_error: str | None = None
    target_platforms: list[str] = Field(default_factory=list)  # empty = no restriction, post everywhere connected


class VariantPromptUpdate(BaseModel):
    image_prompt: str
    motion_prompt: str | None = None
    voiceover_script: str | None = None
    voice_instructions: str | None = None
    music_prompt: str | None = None


class GenerateMediaRequest(BaseModel):
    variant_ids: list[str] = Field(..., min_length=1, description="Variants (from this campaign) to generate media for")


class CaptionOut(BaseModel):
    id: str
    variant_id: str
    platform: str
    caption_text: str
    hashtags: list[str]


class CaptionUpdate(BaseModel):
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


class MetricsSnapshotOut(BaseModel):
    """One `post_metrics` row, with enough context (platform, which variant/post)
    to plot as one point on the metrics graph without extra client-side lookups."""

    id: str
    post_id: str
    variant_id: str
    platform: str
    likes: int
    comments: int
    shares: int
    views: int
    engagement_score: int
    fetched_at: datetime


class PostingTimeRecommendation(BaseModel):
    platform: str
    recommended_hour_utc: int | None
    data_points: int
    confidence: Literal["insufficient_data", "low", "medium", "high"]
