import logging
from typing import Any

from supabase import Client

from ..services import image_gen, llm, usage
from ..services.files import download_asset, rasterize_pdf_pages
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


def _upload_image(client: Client, *, user_id: str, campaign_id: str, variant_index: int, image_bytes: bytes) -> str:
    path = f"{user_id}/{campaign_id}/{variant_index}.png"
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
) -> tuple[list[tuple[bytes, str]], list[str]]:
    """Gathers real reference images to give the image generator directly — the
    brand's identified logo/mascot page(s)/image(s) and every usable product photo,
    brand-first then product, capped at OpenAI's 16-image total. Returns matching
    (images, kinds) lists so callers know which image is which."""
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

    if len(images) > MAX_TOTAL_REFERENCES:
        logger.warning(
            "Total reference images (%d) exceeds OpenAI's edit limit of %d — using only the first %d.",
            len(images),
            MAX_TOTAL_REFERENCES,
            MAX_TOTAL_REFERENCES,
        )
        images = images[:MAX_TOTAL_REFERENCES]
        kinds = kinds[:MAX_TOTAL_REFERENCES]

    return images, kinds


def _generate_one_variant(
    client: Client,
    *,
    user_id: str,
    campaign_id: str,
    variant_index: int,
    angle: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None,
    reference_images: list[tuple[bytes, str]],
    reference_kinds: list[str],
    campaign_type: str,
) -> dict[str, Any]:
    retry_notes: str | None = None
    attempts = 0
    passed = False
    notes = ""
    image_prompt = ""
    image_bytes = b""

    while attempts <= MAX_QUALITY_RETRIES:
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
            logger.info(
                "Variant %d: generating via images.edit with reference(s): %s",
                variant_index,
                reference_kinds,
            )
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
        client, user_id=user_id, campaign_id=campaign_id, variant_index=variant_index, image_bytes=image_bytes
    )

    row = (
        client.table("variants")
        .insert(
            {
                "campaign_id": campaign_id,
                "message_angle": angle,
                "image_prompt": image_prompt,
                "image_url": image_url,
                "quality_check_status": "passed" if passed else "failed_max_retries",
                "quality_check_attempts": attempts,
                "quality_check_notes": notes,
            }
        )
        .execute()
    )
    return row.data[0]


def run_variant_generation(client: Client, *, user_id: str, campaign: dict[str, Any]) -> list[dict[str, Any]]:
    campaign_id = campaign["id"]
    brand = client.table("brands").select("extracted_profile").eq("id", campaign["brand_id"]).single().execute()
    brand_profile = brand.data["extracted_profile"] or {}

    product_profile: dict[str, Any] | None = None
    if campaign.get("product_id"):
        product = (
            client.table("products").select("extracted_profile").eq("id", campaign["product_id"]).single().execute()
        )
        product_profile = product.data["extracted_profile"] or None

    reference_images, reference_kinds = _get_reference_images(client, campaign)
    logger.info(
        "Step 2 for campaign %s: product_id=%s, image mode=%s",
        campaign_id,
        campaign.get("product_id"),
        f"images.edit with reference(s) {reference_kinds}" if reference_images else "text-only (images.generate)",
    )

    client.table("campaigns").update({"status": "generating_variants"}).eq("id", campaign_id).execute()

    try:
        angles, ideation_tokens = llm.ideate_message_angles(
            brand_profile=brand_profile,
            product_profile=product_profile,
            campaign_type=campaign["campaign_type"],
            brief=campaign["brief"],
            n=campaign["variant_count"],
        )
        usage.log_usage(client, user_id=user_id, campaign_id=campaign_id, kind="llm_call", units=ideation_tokens)

        variants = [
            _generate_one_variant(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                variant_index=i,
                angle=angle,
                brand_profile=brand_profile,
                product_profile=product_profile,
                reference_images=reference_images,
                reference_kinds=reference_kinds,
                campaign_type=campaign["campaign_type"],
            )
            for i, angle in enumerate(angles)
        ]

        client.table("campaigns").update({"status": "awaiting_approval"}).eq("id", campaign_id).execute()
        return variants
    except Exception as exc:  # noqa: BLE001
        client.table("campaigns").update(
            {"status": "failed", "error_message": f"Step 2 (variant generation) failed: {exc}"}
        ).eq("id", campaign_id).execute()
        raise
