import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from supabase import Client

from ..config import get_settings
from ..services import audio_mix, elevenlabs_music, elevenlabs_tts, image_gen, llm, luma, usage
from ..services.files import download_asset, rasterize_pdf_pages
from ..services.scheduler import schedule_video_generation_poll
from .product_intake import PRODUCT_ASSETS_BUCKET
from .step1_intake import BRAND_ASSETS_BUCKET

logger = logging.getLogger(__name__)

MAX_QUALITY_RETRIES = 2
VARIANTS_BUCKET = "campaign-variants"

# OpenAI's edit endpoint accepts up to 16 reference images total, combined across brand
# + product. We cap here so a campaign with many uploads never sends more than that.
MAX_TOTAL_REFERENCES = 16

# Safety backstop, independent of the extraction prompt: even if Claude over-flags
# logo/mascot pages in a PDF (e.g. it repeats as a header on nearly every page), never
# rasterize more than this many pages from one PDF as references. Keeps a single
# mis-extracted brand from generating a huge, slow images.edit request.
MAX_PDF_PAGES_PER_SOURCE = 3


def _download_bytes(url: str) -> bytes:
    resp = httpx.get(url, timeout=120)
    resp.raise_for_status()
    return resp.content


def _upload_variant_video(client: Client, *, user_id: str, campaign_id: str, variant_id: str, video_bytes: bytes) -> str:
    path = f"{user_id}/{campaign_id}/{variant_id}.mp4"
    client.storage.from_(VARIANTS_BUCKET).upload(
        path, video_bytes, {"content-type": "video/mp4", "upsert": "true"}
    )
    return client.storage.from_(VARIANTS_BUCKET).get_public_url(path)


def _generate_and_mux_audio(
    client: Client, *, campaign: dict[str, Any], variant: dict[str, Any], video_bytes: bytes
) -> tuple[bytes, str | None]:
    """Generates whichever of voiceover / background music this campaign opted
    into (independently — either, both, or in principle neither, though the
    caller only reaches here when at least one is on) and muxes the result onto
    the video.

    Returns (video_bytes_with_audio, partial_error). `partial_error` is set
    whenever one of the two failed but the other still produced usable audio —
    the video ships with whatever audio it *did* get, but the caller must not
    treat that as a silent full success: a request for "voiceover + music" that
    quietly ships voiceover-only is exactly the kind of failure that looks fine
    until someone actually listens (this is what happened before this function
    returned partial_error — a failed music call left variants.audio_gen_error
    untouched, so nothing anywhere recorded that music had been requested and
    not delivered). Raises only when NEITHER voiceover nor music produced
    anything — the caller then has truly nothing to mux and ships the silent
    video, recording the failure as before."""
    if not audio_mix.is_available():
        raise RuntimeError("ffmpeg is not installed / not on PATH — cannot mix or mux audio onto video.")

    settings = get_settings()
    errors: list[str] = []

    voiceover_bytes: bytes | None = None
    if campaign.get("include_voiceover") and variant.get("voiceover_script"):
        if not settings.elevenlabs_enabled:
            errors.append("voiceover requested but ELEVENLABS_API_KEY is not configured")
        else:
            try:
                brand = (
                    client.table("brands").select("voice_id").eq("id", campaign["brand_id"]).single().execute().data
                )
                voice_id = (brand or {}).get("voice_id")
                voiceover_bytes = elevenlabs_tts.generate_voiceover(variant["voiceover_script"], voice_id=voice_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Voiceover generation failed for variant %s.", variant["id"])
                errors.append(f"voiceover failed: {exc}")

    music_bytes: bytes | None = None
    if campaign.get("include_music") and variant.get("music_prompt"):
        if not settings.elevenlabs_enabled:
            errors.append("music requested but ELEVENLABS_API_KEY is not configured")
        else:
            try:
                music_bytes = elevenlabs_music.generate_music(
                    variant["music_prompt"], length_ms=int(luma.VIDEO_DURATION_SECONDS * 1000)
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Music generation failed for variant %s.", variant["id"])
                errors.append(f"music failed: {exc}")

    mixed = audio_mix.mix_and_mux(video_bytes, voiceover_bytes, music_bytes)  # raises only if both are None
    return mixed, "; ".join(errors) if errors else None


def poll_video_generation_job(variant_id: str, deadline_iso: str) -> None:
    """Entry point for the recurring background poll (services/scheduler.py,
    schedule_video_generation_poll). Builds its own client — same no-HTTP-context
    situation as the feedback/metrics scheduled jobs. Self-cancels by removing its
    own APScheduler job once the Luma request reaches a terminal status, or
    once past `deadline_iso` with no resolution (marked failed rather than left
    stuck in 'generating' forever)."""
    from ..db import get_service_client
    from ..services.scheduler import get_scheduler

    job_id = f"video-poll-{variant_id}"

    def _remove_job() -> None:
        try:
            get_scheduler().remove_job(job_id)
        except Exception:  # noqa: BLE001 - already removed / never existed, nothing to do
            pass

    try:
        client = get_service_client()
        rows = client.table("variants").select("*").eq("id", variant_id).execute().data
        if not rows:
            _remove_job()
            return
        variant = rows[0]

        if variant.get("generation_status") != "generating" or not variant.get("video_gen_job_id"):
            # Already resolved by a previous tick (or never actually started) — nothing to do.
            _remove_job()
            return

        status_data = luma.check_job_status(variant["video_gen_job_id"])
        state = status_data.get("state")

        if state == "completed":
            output = status_data.get("output") or []
            video_url = output[0]["url"] if output and output[0].get("url") else None
            if not video_url:
                client.table("variants").update(
                    {"generation_status": "failed", "video_gen_error": "Luma reported completed with no video URL"}
                ).eq("id", variant_id).execute()
            else:
                campaign = (
                    client.table("campaigns")
                    .select("user_id, brand_id, include_voiceover, include_music")
                    .eq("id", variant["campaign_id"])
                    .single()
                    .execute()
                    .data
                )
                # Luma's output URL is presigned and expires after 1 hour — this download
                # must happen promptly on the first tick that sees 'completed', not deferred.
                video_bytes = _download_bytes(video_url)

                audio_gen_error: str | None = None
                if campaign.get("include_voiceover") or campaign.get("include_music"):
                    try:
                        video_bytes, audio_gen_error = _generate_and_mux_audio(
                            client, campaign=campaign, variant=variant, video_bytes=video_bytes
                        )
                    except Exception as exc:  # noqa: BLE001
                        # Audio is an enhancement on top of the video, not the core deliverable —
                        # a failed voiceover/mix ships the silent video rather than blocking the
                        # whole variant, same "non-fatal add-on" pattern as reference-image warnings.
                        # (Reached only when NEITHER voiceover nor music produced anything at all —
                        # a partial failure with the other succeeding comes back as audio_gen_error
                        # above instead, not an exception.)
                        logger.exception(
                            "Audio generation/mux failed for variant %s — shipping silent video instead.",
                            variant_id,
                        )
                        audio_gen_error = str(exc)

                stored_url = _upload_variant_video(
                    client,
                    user_id=campaign["user_id"],
                    campaign_id=variant["campaign_id"],
                    variant_id=variant_id,
                    video_bytes=video_bytes,
                )
                update: dict[str, Any] = {"video_url": stored_url, "generation_status": "generated"}
                if audio_gen_error:
                    update["audio_gen_error"] = audio_gen_error
                client.table("variants").update(update).eq("id", variant_id).execute()
            _remove_job()
            return

        if state == "failed":
            error = status_data.get("failure_reason") or f"Video generation failed ({status_data.get('failure_code')})"
            client.table("variants").update(
                {"generation_status": "failed", "video_gen_error": error}
            ).eq("id", variant_id).execute()
            _remove_job()
            return

        # Still queued/processing. Only the timeout backstop can end this tick's work.
        if datetime.fromisoformat(deadline_iso) <= datetime.now(timezone.utc):
            client.table("variants").update(
                {"generation_status": "failed", "video_gen_error": "Video generation timed out"}
            ).eq("id", variant_id).execute()
            _remove_job()
    except Exception:  # noqa: BLE001
        # A transient failure (network blip, DB hiccup) shouldn't kill the polling job —
        # leave it running so the next tick just tries again; the deadline check above
        # is what eventually stops it for real if Luma never resolves.
        logger.exception("Video generation poll failed for variant %s", variant_id)


def _upload_image(client: Client, *, user_id: str, campaign_id: str, variant_id: str, image_bytes: bytes) -> str:
    # Keyed by variant_id (not a positional index) — generation now happens per-variant,
    # possibly for an arbitrary subset chosen after review, so there's no stable index
    # to rely on any more.
    path = f"{user_id}/{campaign_id}/{variant_id}.png"
    client.storage.from_(VARIANTS_BUCKET).upload(
        path, image_bytes, {"content-type": "image/png", "upsert": "true"}
    )
    return client.storage.from_(VARIANTS_BUCKET).get_public_url(path)


def _build_targeted_pdf_pages(extracted_profile: dict[str, Any] | None) -> dict[str, list[int]]:
    """Maps each PDF's storage path to the specific page number(s) Claude identified
    (in `logo_mascot_pages`, against the `source_files` order it saw) as clearly
    showing the brand's logo/mascot. A PDF with no entry here means Claude didn't find
    a distinct logo/mascot page in it — its colors/typography/etc. are already in the
    text profile, so it's skipped as a visual reference rather than guessed at."""
    if not extracted_profile:
        return {}
    source_files: list[str] = extracted_profile.get("source_files", [])
    entries: list[dict[str, Any]] = extracted_profile.get("logo_mascot_pages", [])

    result: dict[str, list[int]] = {}
    for entry in entries:
        file_index, page_number = entry.get("file_index"), entry.get("page_number")
        if file_index is None or page_number is None or not (0 <= file_index < len(source_files)):
            continue
        path = source_files[file_index]
        result.setdefault(path, [])
        if page_number not in result[path]:
            result[path].append(page_number)

    for path, pages in result.items():
        if len(pages) > MAX_PDF_PAGES_PER_SOURCE:
            logger.warning(
                "Brand PDF '%s' had %d logo/mascot pages identified — capping to the first %d to avoid "
                "an oversized image-gen request. (If this keeps happening, the extraction prompt may "
                "need tightening further.)",
                path,
                len(pages),
                MAX_PDF_PAGES_PER_SOURCE,
            )
            result[path] = pages[:MAX_PDF_PAGES_PER_SOURCE]

    return result


def _load_edit_references(
    client: Client,
    *,
    bucket: str,
    asset_paths: list[str] | None,
    label: str,
    targeted_pdf_pages: dict[str, list[int]] | None = None,
) -> list[tuple[bytes, str]]:
    """Shared logic for both brand and product references: download every uploaded
    asset for this source and turn each into something OpenAI's edit endpoint can use
    (PNG/JPG/WebP directly; a PDF gets rasterized into page images first, since the
    edit endpoint doesn't accept PDFs even though Claude's text extraction does).
    GIFs and anything else are skipped, with a warning logged.

    For PDFs specifically: if `targeted_pdf_pages` is given (the brand case), only the
    page(s) Claude identified as showing the logo/mascot are rasterized — a PDF with no
    identified page is skipped entirely as a visual reference (not guessed at). If
    `targeted_pdf_pages` is None (the product case, where there's no logo/mascot-style
    targeting), falls back to blindly rasterizing the first couple of pages."""
    refs: list[tuple[bytes, str]] = []
    for path in asset_paths or []:
        file_bytes, media_type = download_asset(client, bucket, path)
        if not file_bytes or not media_type:
            continue

        if image_gen.supports_edit_reference(media_type):
            refs.append((file_bytes, media_type))
        elif media_type == "application/pdf":
            if targeted_pdf_pages is not None:
                pages = targeted_pdf_pages.get(path, [])
                if not pages:
                    logger.info(
                        "%s PDF '%s': no logo/mascot page identified — using its text profile only, "
                        "not as a visual reference.",
                        label,
                        path,
                    )
                    continue
                logger.info("%s PDF '%s': rasterizing identified logo/mascot page(s) %s.", label, path, pages)
                try:
                    refs.extend(rasterize_pdf_pages(file_bytes, page_numbers=pages))
                except Exception:
                    logger.exception("Failed to rasterize targeted page(s) of PDF '%s' — skipping.", path)
            else:
                logger.info(
                    "%s asset '%s' is a PDF — rasterizing first page(s) to use as an image-gen reference.",
                    label,
                    path,
                )
                try:
                    refs.extend(rasterize_pdf_pages(file_bytes))
                except Exception:
                    logger.exception("Failed to rasterize PDF asset '%s' — skipping it as a reference.", path)
        else:
            logger.warning(
                "%s asset '%s' (%s) isn't usable as an image-gen reference (PNG/JPG/WebP/PDF only) — "
                "skipping it.",
                label,
                path,
                media_type,
            )
    return refs


def _get_reference_images(
    client: Client, campaign: dict[str, Any]
) -> tuple[list[tuple[bytes, str]], list[str], str | None]:
    """Gathers real reference images to give the image generator directly — the
    brand's identified logo/mascot page(s)/image(s) and every usable product photo,
    brand-first then product, capped at OpenAI's 16-image total. Returns matching
    (images, kinds) lists so callers know which image is which, plus a user-facing
    warning (or None) if the cap actually truncated something — brand's real
    reference count isn't known until this point (it depends on what Claude's
    extraction found), so this can't be validated any earlier than here.

    Called once during ideation (to inform prompt-writing and surface the warning)
    and again during generation (to actually feed the image editor) — a repeated
    storage read, not a repeated paid call, so recomputing rather than caching is
    the simpler choice here."""
    images: list[tuple[bytes, str]] = []
    kinds: list[str] = []

    brand = (
        client.table("brands")
        .select("guideline_assets, extracted_profile")
        .eq("id", campaign["brand_id"])
        .single()
        .execute()
    )
    targeted_pages = _build_targeted_pdf_pages(brand.data.get("extracted_profile"))
    brand_refs = _load_edit_references(
        client,
        bucket=BRAND_ASSETS_BUCKET,
        asset_paths=brand.data["guideline_assets"],
        label="Brand guideline",
        targeted_pdf_pages=targeted_pages,
    )
    images.extend(brand_refs)
    kinds.extend(["brand"] * len(brand_refs))

    if campaign.get("product_id"):
        product = client.table("products").select("asset_paths").eq("id", campaign["product_id"]).single().execute()
        product_refs = _load_edit_references(
            client, bucket=PRODUCT_ASSETS_BUCKET, asset_paths=product.data["asset_paths"], label="Product"
        )
        images.extend(product_refs)
        kinds.extend(["product"] * len(product_refs))

    warning: str | None = None
    if len(images) > MAX_TOTAL_REFERENCES:
        dropped_kinds = kinds[MAX_TOTAL_REFERENCES:]
        dropped_product = dropped_kinds.count("product")
        dropped_brand = dropped_kinds.count("brand")
        logger.warning(
            "Total reference images (%d) exceeds OpenAI's edit limit of %d — using only the first %d.",
            len(images),
            MAX_TOTAL_REFERENCES,
            MAX_TOTAL_REFERENCES,
        )
        parts = []
        if dropped_product:
            parts.append(f"{dropped_product} product photo(s)")
        if dropped_brand:
            parts.append(f"{dropped_brand} brand reference(s)")
        warning = (
            f"Your brand and product references together ({len(images)}) exceeded the 16-image limit "
            f"the AI can use at once, so {' and '.join(parts)} weren't included in generation."
        )
        images = images[:MAX_TOTAL_REFERENCES]
        kinds = kinds[:MAX_TOTAL_REFERENCES]

    return images, kinds, warning


def _load_profiles(client: Client, campaign: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    brand = client.table("brands").select("extracted_profile").eq("id", campaign["brand_id"]).single().execute()
    brand_profile = brand.data["extracted_profile"] or {}

    product_profile: dict[str, Any] | None = None
    if campaign.get("product_id"):
        product = (
            client.table("products").select("extracted_profile").eq("id", campaign["product_id"]).single().execute()
        )
        product_profile = product.data["extracted_profile"] or None

    return brand_profile, product_profile


# ---------------------------------------------------------------------------
# Ideation — cheap, LLM-only. Produces a `variants` row per message angle with
# prompt(s) filled in but no media generated yet, so the user can review/edit
# before any image-gen/video-gen cost is spent. Campaign lands in
# 'awaiting_prompt_review', not 'awaiting_approval' — that status is reserved
# for "media exists, review it for posting."
# ---------------------------------------------------------------------------
def ideate_variants(client: Client, *, user_id: str, campaign: dict[str, Any]) -> list[dict[str, Any]]:
    campaign_id = campaign["id"]
    media_type = campaign.get("media_type", "image")
    include_voiceover = media_type == "video" and campaign.get("include_voiceover", False)
    include_music = media_type == "video" and campaign.get("include_music", False)
    include_audio = include_voiceover or include_music
    brand_profile, product_profile = _load_profiles(client, campaign)
    reference_images, reference_kinds, reference_warning = _get_reference_images(client, campaign)
    logger.info(
        "Step 2 ideation for campaign %s: product_id=%s, media_type=%s, image mode=%s",
        campaign_id,
        campaign.get("product_id"),
        media_type,
        f"images.edit with reference(s) {reference_kinds}" if reference_images else "text-only (images.generate)",
    )

    update: dict[str, Any] = {"status": "awaiting_prompt_review"}
    if reference_warning:
        update["warning_message"] = reference_warning
    client.table("campaigns").update(update).eq("id", campaign_id).execute()

    try:
        angles, ideation_tokens = llm.ideate_message_angles(
            brand_profile=brand_profile,
            product_profile=product_profile,
            campaign_type=campaign["campaign_type"],
            brief=campaign["brief"],
            n=campaign["variant_count"],
        )
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=ideation_tokens)

        variants = []
        for angle in angles:
            image_prompt, prompt_tokens = llm.write_image_prompt(
                angle=angle,
                brand_profile=brand_profile,
                product_profile=product_profile,
                reference_kinds=reference_kinds,
                campaign_type=campaign["campaign_type"],
            )
            usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=prompt_tokens)

            motion_prompt: str | None = None
            if media_type == "video":
                motion_prompt, motion_tokens = llm.ideate_motion_prompt(
                    angle=angle,
                    image_prompt=image_prompt,
                    brand_profile=brand_profile,
                    product_profile=product_profile,
                    campaign_type=campaign["campaign_type"],
                )
                usage.log_usage(
                    client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=motion_tokens
                )

            audio_fields: dict[str, str | None] = {
                "voiceover_script": None,
                "voice_instructions": None,
                "music_prompt": None,
            }
            if include_audio:
                audio_script, audio_tokens = llm.write_audio_script(
                    angle=angle,
                    image_prompt=image_prompt,
                    brand_profile=brand_profile,
                    product_profile=product_profile,
                    campaign_type=campaign["campaign_type"],
                    duration_seconds=luma.VIDEO_DURATION_SECONDS,
                )
                usage.log_usage(
                    client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=audio_tokens
                )
                audio_fields = audio_script  # {voiceover_script, voice_instructions, music_prompt}

            row = (
                client.table("variants")
                .insert(
                    {
                        "campaign_id": campaign_id,
                        "message_angle": angle,
                        "image_prompt": image_prompt,
                        "motion_prompt": motion_prompt,
                        "media_type": media_type,
                        "generation_status": "awaiting_prompt_review",
                        **audio_fields,
                    }
                )
                .execute()
            )
            variants.append(row.data[0])

        return variants
    except Exception as exc:  # noqa: BLE001
        client.table("campaigns").update(
            {"status": "failed", "error_message": f"Step 2 (ideation) failed: {exc}"}
        ).eq("id", campaign_id).execute()
        raise


def _start_video_generation(
    client: Client, *, user_id: str, campaign_id: str, variant_id: str, image_bytes: bytes, motion_prompt: str
) -> None:
    """Submits the starting image + motion prompt to Luma and registers a polling
    job to pick up completion — never raises: a submission failure (missing key, or
    the API call itself failing) is recorded on the variant as
    generation_status='failed' with video_gen_error, same "gated, not broken" pattern
    used for unconfigured social OAuth."""
    settings = get_settings()
    if not settings.luma_enabled:
        client.table("variants").update(
            {
                "generation_status": "failed",
                "video_gen_error": "Video generation is not configured (missing Luma API key).",
            }
        ).eq("id", variant_id).execute()
        return

    try:
        job_id = luma.submit_image_to_video(image_bytes, motion_prompt)
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="video_gen", units=1)
        client.table("variants").update({"video_gen_job_id": job_id}).eq("id", variant_id).execute()
        schedule_video_generation_poll(variant_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to submit video generation job for variant %s", variant_id)
        client.table("variants").update(
            {"generation_status": "failed", "video_gen_error": str(exc)}
        ).eq("id", variant_id).execute()


def _generate_media_for_variant(
    client: Client,
    *,
    user_id: str,
    campaign_id: str,
    variant: dict[str, Any],
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None,
    reference_images: list[tuple[bytes, str]],
    reference_kinds: list[str],
    campaign_type: str,
) -> dict[str, Any]:
    """The expensive step for one variant, run only once the user has confirmed
    (possibly edited) its prompt. Reuses the same quality-check retry loop as
    before, but attempt 1 uses the given prompt as-is — no LLM call — and only
    retries 2+ fall back to normal LLM re-prompting via retry_notes, same as
    today. For a video variant, the starting image still goes through the full
    quality-check loop unchanged; only once it passes does this hand off to
    Luma for animation."""
    variant_id = variant["id"]
    media_type = variant.get("media_type", "image")
    angle = variant["message_angle"]

    retry_notes: str | None = None
    attempts = 0
    passed = False
    notes = ""
    image_prompt = variant["image_prompt"]
    image_bytes = b""

    while attempts <= MAX_QUALITY_RETRIES:
        if attempts > 0:
            image_prompt, prompt_tokens = llm.write_image_prompt(
                angle=angle,
                brand_profile=brand_profile,
                product_profile=product_profile,
                reference_kinds=reference_kinds,
                campaign_type=campaign_type,
                retry_notes=retry_notes,
            )
            usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=prompt_tokens)

        if reference_images:
            image_bytes = image_gen.edit_image_with_references(image_prompt, reference_images)
        else:
            image_bytes = image_gen.generate_image(image_prompt)
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="image_gen", units=1)

        passed, notes, check_tokens = llm.check_image_quality(
            image_bytes=image_bytes,
            media_type="image/png",
            brand_profile=brand_profile,
            product_profile=product_profile,
            reference_images=reference_images,
            reference_kinds=reference_kinds,
        )
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=check_tokens)

        attempts += 1
        if passed:
            break
        retry_notes = notes

    image_url = _upload_image(
        client, user_id=user_id, campaign_id=campaign_id, variant_id=variant_id, image_bytes=image_bytes
    )

    update: dict[str, Any] = {
        "image_prompt": image_prompt,
        "image_url": image_url,
        "quality_check_status": "passed" if passed else "failed_max_retries",
        "quality_check_attempts": attempts,
        "quality_check_notes": notes,
    }

    if media_type == "video":
        update["generation_status"] = "generating"
        client.table("variants").update(update).eq("id", variant_id).execute()
        _start_video_generation(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            variant_id=variant_id,
            image_bytes=image_bytes,
            motion_prompt=variant.get("motion_prompt") or "",
        )
        return client.table("variants").select("*").eq("id", variant_id).single().execute().data

    update["generation_status"] = "generated"
    row = client.table("variants").update(update).eq("id", variant_id).execute()
    return row.data[0]


# ---------------------------------------------------------------------------
# Generation — the expensive step, run only for the variants the user selected
# to keep after reviewing their (possibly edited) prompts. Deselected variants
# are deleted here, never generated — the actual cost-saving point of this
# whole ideate/generate split.
# ---------------------------------------------------------------------------
def generate_variant_media(client: Client, *, user_id: str, campaign: dict[str, Any], variant_ids: list[str]) -> list[dict[str, Any]]:
    campaign_id = campaign["id"]
    brand_profile, product_profile = _load_profiles(client, campaign)
    reference_images, reference_kinds, _ = _get_reference_images(client, campaign)

    all_variants = client.table("variants").select("id").eq("campaign_id", campaign_id).execute().data
    deselected_ids = [v["id"] for v in all_variants if v["id"] not in variant_ids]
    if deselected_ids:
        client.table("variants").delete().in_("id", deselected_ids).execute()

    variants = client.table("variants").select("*").eq("campaign_id", campaign_id).in_("id", variant_ids).execute().data
    if not variants:
        raise ValueError("No matching variants selected to generate")

    client.table("campaigns").update({"status": "generating_variants"}).eq("id", campaign_id).execute()

    try:
        results = [
            _generate_media_for_variant(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                variant=variant,
                brand_profile=brand_profile,
                product_profile=product_profile,
                reference_images=reference_images,
                reference_kinds=reference_kinds,
                campaign_type=campaign["campaign_type"],
            )
            for variant in variants
        ]

        client.table("campaigns").update({"status": "awaiting_approval"}).eq("id", campaign_id).execute()
        return results
    except Exception as exc:  # noqa: BLE001
        client.table("campaigns").update(
            {"status": "failed", "error_message": f"Step 2 (media generation) failed: {exc}"}
        ).eq("id", campaign_id).execute()
        raise
