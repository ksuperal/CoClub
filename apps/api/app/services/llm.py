"""Anthropic Claude wrapper for every text/vision step in the pipeline.

Structured output is obtained via forced tool use (a single tool whose input schema
is the shape we want) rather than asking the model to "return JSON" in prose — this
is the reliable way to get parseable structured data out of Claude.
"""

import base64
from typing import Any

import anthropic

from ..config import get_settings


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=get_settings().anthropic_api_key)


def _forced_tool_call(
    *, system: str, messages: list[dict[str, Any]], tool: dict[str, Any], max_tokens: int = 2000
) -> tuple[dict[str, Any], int]:
    """Runs one Claude call forced to use `tool`, returns (tool_input, output_tokens)."""
    settings = get_settings()
    resp = _client().messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
    )
    for block in resp.content:
        if block.type == "tool_use":
            return block.input, resp.usage.output_tokens
    raise RuntimeError("Claude did not return a tool_use block")


def _primary_secondary_content(
    *,
    file_bytes: bytes | None,
    file_media_type: str | None,
    text: str | None,
    file_caption: str,
    text_caption: str,
    empty_caption: str,
) -> list[dict[str, Any]]:
    """Builds one message's content blocks so an uploaded file (if any) is sent as the
    primary source and free text as supplementary — used by both brand and product
    extraction so "prioritize the upload, but still consider the text" is one rule,
    not two separately-maintained ones."""
    content: list[dict[str, Any]] = []
    if file_bytes and file_media_type:
        block_type = "document" if file_media_type == "application/pdf" else "image"
        content.append(
            {
                "type": block_type,
                "source": {
                    "type": "base64",
                    "media_type": file_media_type,
                    "data": base64.b64encode(file_bytes).decode("utf-8"),
                },
            }
        )
        content.append({"type": "text", "text": file_caption})
    if text:
        content.append({"type": "text", "text": f"{text_caption}\n\n{text}"})
    if not content:
        content.append({"type": "text", "text": empty_caption})
    return content


# ---------------------------------------------------------------------------
# Step 1: brand intake — structured extraction with citations.
#
# If an uploaded guideline file (image or PDF) is available, it's sent as the
# primary source and pasted text is treated as supplementary — the file wins
# on any conflict. Output shape is fixed to mascot/color/guideline/font/
# product/style so every downstream step can rely on those exact keys.
# ---------------------------------------------------------------------------
def extract_brand_profile(
    guideline_text: str, *, file_bytes: bytes | None = None, file_media_type: str | None = None
) -> tuple[dict[str, Any], int]:
    tool = {
        "name": "record_brand_profile",
        "description": "Record the structured brand profile extracted from the brand guideline material.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mascot": {
                    "type": "string",
                    "description": "The brand's mascot/character, if any — name, appearance, personality, "
                    "usage rules. Empty string if there is no mascot.",
                },
                "color": {
                    "type": "array",
                    "description": "The brand's color palette.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "hex": {"type": "string"},
                            "name": {"type": "string"},
                            "usage": {"type": "string", "description": "e.g. primary, accent, background"},
                        },
                        "required": ["hex"],
                    },
                },
                "guideline": {
                    "type": "string",
                    "description": "Consolidated brand voice/tone and do's-and-don'ts guidance.",
                },
                "font": {
                    "type": "array",
                    "description": "Typography used by the brand.",
                    "items": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}, "usage": {"type": "string"}},
                        "required": ["name"],
                    },
                },
                "product": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Products/services this brand offers.",
                },
                "style": {
                    "type": "string",
                    "description": "Overall visual style — e.g. minimalist, playful, photography vs "
                    "illustration, imagery mood.",
                },
                "citations": {
                    "type": "array",
                    "description": "For each extracted fact, where it came from in the source material.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string"},
                            "source_quote": {"type": "string"},
                        },
                        "required": ["fact", "source_quote"],
                    },
                },
            },
            "required": ["mascot", "color", "guideline", "font", "product", "style", "citations"],
        },
    }
    system = (
        "You extract a structured brand profile — mascot, color, guideline, font, product, style — from "
        "brand guideline material. If both an uploaded document/image and pasted text are given, the "
        "uploaded document is the authoritative primary source; treat the pasted text as supplementary "
        "and defer to the document wherever the two conflict. Every fact must be traceable to the source "
        "material — do not infer facts it doesn't support."
    )

    content = _primary_secondary_content(
        file_bytes=file_bytes,
        file_media_type=file_media_type,
        text=guideline_text,
        file_caption="Brand guideline document above — this is the primary source.",
        text_caption="Supplementary notes from the user (secondary source):",
        empty_caption="No brand guideline material was provided.",
    )
    messages = [{"role": "user", "content": content}]
    return _forced_tool_call(system=system, messages=messages, tool=tool, max_tokens=3000)


# ---------------------------------------------------------------------------
# Product intake — structured extraction with citations, mirroring brand intake.
# The upload is required (checked by the router before this is ever called) since
# the product photo is the ground truth for what the product actually looks like;
# the text description is supplementary, same priority rule as brand intake.
# ---------------------------------------------------------------------------
def extract_product_profile(
    description_text: str | None, *, file_bytes: bytes, file_media_type: str
) -> tuple[dict[str, Any], int]:
    tool = {
        "name": "record_product_profile",
        "description": "Record the structured product profile extracted from the product material.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "key_features": {"type": "array", "items": {"type": "string"}},
                "selling_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Marketing-relevant benefits/hooks this product supports.",
                },
                "visual_description": {
                    "type": "string",
                    "description": "Literal visual description of the product itself — shape, material, "
                    "color, size — precise enough to reference directly in an image-generation prompt.",
                },
                "citations": {
                    "type": "array",
                    "description": "For each extracted fact, where it came from in the source material.",
                    "items": {
                        "type": "object",
                        "properties": {"fact": {"type": "string"}, "source_quote": {"type": "string"}},
                        "required": ["fact", "source_quote"],
                    },
                },
            },
            "required": ["category", "key_features", "selling_points", "visual_description", "citations"],
        },
    }
    system = (
        "You extract a structured product profile — category, key_features, selling_points, "
        "visual_description — from product material (a photo/file and optionally a text description). "
        "The uploaded photo/file is the authoritative primary source, especially for visual_description; "
        "treat the text description as supplementary and defer to the file wherever the two conflict. "
        "Every fact must be traceable to the source material."
    )
    content = _primary_secondary_content(
        file_bytes=file_bytes,
        file_media_type=file_media_type,
        text=description_text,
        file_caption="Product photo/file above — this is the primary source.",
        text_caption="Supplementary product description from the user (secondary source):",
        empty_caption="No product material was provided.",
    )
    messages = [{"role": "user", "content": content}]
    return _forced_tool_call(system=system, messages=messages, tool=tool, max_tokens=2000)


# ---------------------------------------------------------------------------
# Step 2a: ideation — message angles (separated from execution for diversity)
# ---------------------------------------------------------------------------
def ideate_message_angles(
    *,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    campaign_type: str,
    brief: str,
    n: int,
) -> tuple[list[str], int]:
    tool = {
        "name": "record_angles",
        "description": "Record N distinct message angles for this campaign.",
        "input_schema": {
            "type": "object",
            "properties": {
                "angles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Each angle is a distinct emotional/strategic hook, one sentence.",
                }
            },
            "required": ["angles"],
        },
    }
    system = (
        "You are a marketing strategist. Given a brand profile and campaign brief, propose "
        f"exactly {n} genuinely distinct message angles (not just reworded restatements of "
        "each other) appropriate for a "
        f"'{campaign_type}' campaign. Stay consistent with the brand's guideline, mascot, and style."
    )
    user_text = f"Brand profile: {brand_profile}\n\n"
    if product_profile:
        user_text += f"Product profile: {product_profile}\n\n"
    user_text += f"Campaign brief: {brief}\n\nPropose {n} distinct message angles."
    messages = [{"role": "user", "content": user_text}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool)
    return result["angles"][:n], tokens


# ---------------------------------------------------------------------------
# Step 2b: execution — turn one angle into an image-gen prompt
# ---------------------------------------------------------------------------
def write_image_prompt(
    *,
    angle: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    has_reference_image: bool = False,
    campaign_type: str,
    retry_notes: str | None = None,
) -> tuple[str, int]:
    tool = {
        "name": "record_image_prompt",
        "description": "Record the image generation prompt for this message angle.",
        "input_schema": {
            "type": "object",
            "properties": {"image_prompt": {"type": "string"}},
            "required": ["image_prompt"],
        },
    }
    if has_reference_image:
        product_instruction = (
            "The actual product photo will be given directly to the image generator as a reference "
            "image alongside your prompt — do NOT describe what the product itself looks like, the "
            "generator already sees the real photo. Instead, describe the SCENE to place it in: "
            "background, composition, lighting, other elements, mood — consistent with the brand and "
            "message angle. Refer to the product simply as 'the product in the reference image'."
        )
    elif product_profile:
        product_instruction = (
            "No reference photo is available — the product's visual_description is what the product "
            "must actually look like in the image. Render it faithfully, don't invent a "
            "different-looking product."
        )
    else:
        product_instruction = ""

    system = (
        "You write image-generation prompts for social ad creative. The prompt must faithfully render "
        "the brand's color palette, mascot (if any), and visual style, and fit a "
        f"'{campaign_type}' campaign. Be visually specific — composition, subject, lighting, "
        f"color palette — not just a restatement of the message angle. {product_instruction}"
    )
    user_content = f"Brand profile: {brand_profile}\n\nMessage angle: {angle}"
    if product_profile:
        user_content += f"\n\nProduct profile: {product_profile}"
    if retry_notes:
        user_content += (
            f"\n\nThe previous attempt failed brand-compliance review for this reason: "
            f"{retry_notes}. Adjust the prompt to fix it."
        )
    messages = [{"role": "user", "content": user_content}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool)
    return result["image_prompt"], tokens


# ---------------------------------------------------------------------------
# Step 2c: the one real agent loop — vision-based brand-compliance check
# ---------------------------------------------------------------------------
def check_image_quality(
    *,
    image_bytes: bytes,
    media_type: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    reference_image: tuple[bytes, str] | None = None,
) -> tuple[bool, str, int]:
    """Returns (passed, notes, output_tokens). If `reference_image` (the real product
    photo) is given, it's shown alongside the generated image for a direct visual
    comparison — otherwise the check falls back to comparing against the text
    visual_description only."""
    tool = {
        "name": "record_quality_check",
        "description": "Record the brand-compliance verdict for this generated image.",
        "input_schema": {
            "type": "object",
            "properties": {
                "passed": {"type": "boolean"},
                "notes": {
                    "type": "string",
                    "description": "If failed, the specific reason (e.g. wrong colors, missing "
                    "required element). If passed, brief confirmation.",
                },
            },
            "required": ["passed", "notes"],
        },
    }
    system = (
        "You review a generated ad image against a brand's profile (color, mascot, style, guideline) "
        "and decide pass/fail. Be strict about color palette and mascot adherence. If a product profile "
        "is given, also check the product in the image matches its visual_description — reject if the "
        "image shows a different-looking product. If a reference photo of the real product is also "
        "shown, compare the generated product directly against it (shape, color, proportions, "
        "distinguishing details) rather than relying only on the text description."
    )
    content: list[dict[str, Any]] = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": base64.b64encode(image_bytes).decode("utf-8")},
        }
    ]
    text = f"Generated image above. Brand profile: {brand_profile}\n\n"
    if product_profile:
        text += f"Product profile: {product_profile}\n\n"
    if reference_image:
        ref_bytes, ref_media_type = reference_image
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": ref_media_type,
                    "data": base64.b64encode(ref_bytes).decode("utf-8"),
                },
            }
        )
        text += "Real product reference photo above (second image). "
    text += "Does the generated image comply?"
    content.append({"type": "text", "text": text})
    messages = [{"role": "user", "content": content}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool)
    return result["passed"], result["notes"], tokens


# ---------------------------------------------------------------------------
# Step 3: copywriting — captions + hashtags per platform
# ---------------------------------------------------------------------------
def write_captions(
    *,
    message_angle: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    campaign_type: str,
    platforms: list[str],
) -> tuple[list[dict[str, Any]], int]:
    tool = {
        "name": "record_captions",
        "description": "Record one caption + hashtag set per platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "captions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "platform": {"type": "string"},
                            "caption_text": {"type": "string"},
                            "hashtags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["platform", "caption_text", "hashtags"],
                    },
                }
            },
            "required": ["captions"],
        },
    }
    system = (
        "You write platform-native captions and hashtags for a social ad. Instagram favors "
        "keyword-rich, SEO-style captions; TikTok favors short, high-velocity hashtags; "
        "YouTube and Facebook favor slightly longer, descriptive captions. Match the brand's "
        f"guideline and style, and the '{campaign_type}' campaign type. Be concretely specific to this "
        "product/message — avoid generic filler like 'check this out'."
    )
    user_text = f"Brand profile: {brand_profile}\n\n"
    if product_profile:
        user_text += f"Product profile: {product_profile}\n\n"
    user_text += f"Message angle: {message_angle}\n\nPlatforms: {', '.join(platforms)}"
    messages = [{"role": "user", "content": user_text}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool)
    return result["captions"], tokens


# ---------------------------------------------------------------------------
# Step 5: feedback report — LLM narrates verdicts computed in code, never
# invents numbers itself.
# ---------------------------------------------------------------------------
def narrate_report(
    *, campaign_type: str, verdicts: list[dict[str, Any]]
) -> tuple[str, int]:
    tool = {
        "name": "record_report",
        "description": "Record the narrated campaign performance summary.",
        "input_schema": {
            "type": "object",
            "properties": {"summary_text": {"type": "string"}},
            "required": ["summary_text"],
        },
    }
    system = (
        "You narrate a campaign performance report for a small-business owner. You are given "
        "pre-computed verdicts (already-calculated stats and rankings) — narrate them clearly, "
        "recommend what's worth boosting, and never invent or adjust any number yourself."
    )
    messages = [
        {
            "role": "user",
            "content": f"Campaign type: {campaign_type}\n\nPre-computed verdicts: {verdicts}",
        }
    ]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool, max_tokens=1000)
    return result["summary_text"], tokens
