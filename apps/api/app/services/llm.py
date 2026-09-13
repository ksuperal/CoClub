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
    files: list[tuple[bytes, str]],
    text: str | None,
    file_caption: str,
    text_caption: str,
    empty_caption: str,
) -> list[dict[str, Any]]:
    """Builds one message's content blocks so uploaded file(s) (if any) are sent as the
    primary source and free text as supplementary — used by both brand and product
    extraction so "prioritize the upload(s), but still consider the text" is one rule,
    not two separately-maintained ones. Supports multiple files (e.g. a multi-page
    guideline, or several product photos)."""
    content: list[dict[str, Any]] = []
    if files:
        content.append({"type": "text", "text": file_caption})
        for i, (file_bytes, file_media_type) in enumerate(files):
            block_type = "document" if file_media_type == "application/pdf" else "image"
            content.append(
                {"type": "text", "text": f"File {i} ({'PDF' if block_type == 'document' else 'image'}):"}
            )
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
    guideline_text: str, *, files: list[tuple[bytes, str]] | None = None
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
                "logo_mascot_pages": {
                    "type": "array",
                    "description": "At most 1 page for the logo and at most 2 pages for the mascot, "
                    "total — the SINGLE clearest, most complete standalone presentation of each (e.g. a "
                    "logo spec/showcase page, a mascot model-sheet/reference page). Do NOT include every "
                    "page where the logo happens to appear as a small recurring header/footer/watermark "
                    "— a multi-page guideline typically repeats the logo on nearly every page as a "
                    "template element, and none of those repeats belong here. Only the one or two pages "
                    "that exist specifically TO showcase the artwork itself. For a non-PDF image file, "
                    "page_number is always 1. Leave empty if no file has a genuine standalone showcase.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "file_index": {
                                "type": "integer",
                                "description": "The file's number from 'File N (...)' in the material above.",
                            },
                            "page_number": {
                                "type": "integer",
                                "description": "1-indexed page within that file (always 1 for image files).",
                            },
                            "shows": {"type": "string", "enum": ["logo", "mascot", "both"]},
                        },
                        "required": ["file_index", "page_number", "shows"],
                    },
                },
            },
            "required": [
                "mascot", "color", "guideline", "font", "product", "style", "citations", "logo_mascot_pages"
            ],
        },
    }
    system = (
        "You extract a structured brand profile — mascot, color, guideline, font, product, style — from "
        "brand guideline material. If both an uploaded document/image and pasted text are given, the "
        "uploaded document is the authoritative primary source; treat the pasted text as supplementary "
        "and defer to the document wherever the two conflict. Every fact must be traceable to the source "
        "material — do not infer facts it doesn't support. Also identify the single best file+page (if "
        "any) showing the logo, and the single or two best page(s) showing the mascot — these become "
        "real reference images sent to an image generator, so being selective matters far more than "
        "being exhaustive. A logo that repeats on every page as a template header/footer does NOT "
        "count — only a page whose actual purpose is to showcase the logo/mascot artwork itself."
    )

    content = _primary_secondary_content(
        files=files or [],
        text=guideline_text,
        file_caption="Brand guideline document(s) above — these are the primary source.",
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
    description_text: str | None, *, files: list[tuple[bytes, str]]
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
        files=files,
        text=description_text,
        file_caption="Product photo(s)/file(s) above — these are the primary source.",
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


def _describe_references(reference_kinds: list[str], *, has_product_profile: bool) -> str:
    """Builds the instruction telling Claude which numbered images (1-indexed, in the
    order they'll actually be sent) are brand references vs product references — any
    count of each, not just zero-or-one. References are always sent brand-first then
    product (see step2_variants.py's _get_reference_images), so kinds are contiguous."""
    if not reference_kinds:
        if has_product_profile:
            return (
                "No reference photo is available — the product's visual_description is what the "
                "product must actually look like in the image. Render it faithfully, don't invent a "
                "different-looking product."
            )
        return ""

    def _range(start: int, count: int) -> str:
        return f"image {start}" if count == 1 else f"images {start}-{start + count - 1}"

    brand_count = reference_kinds.count("brand")
    product_count = reference_kinds.count("product")
    parts = []
    idx = 1
    if brand_count:
        parts.append(
            f"{_range(idx, brand_count)}: the brand's visual guideline (colors/mascot/logo) — match "
            "this visual identity exactly wherever it applies, especially the mascot if shown."
        )
        idx += brand_count
    if product_count:
        parts.append(
            f"{_range(idx, product_count)}: the real product — render it faithfully, don't invent a "
            "different-looking product."
        )

    return (
        "Real reference image(s) will be given directly to the image generator alongside your prompt: "
        + " ".join(parts)
        + " Do NOT describe in words what these reference images show — the generator already sees "
        "them. Instead, describe the SCENE: background, composition, lighting, mood, and how these "
        "elements should be combined."
    )


# ---------------------------------------------------------------------------
# Step 2b: execution — turn one angle into an image-gen prompt
# ---------------------------------------------------------------------------
def write_image_prompt(
    *,
    angle: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    reference_kinds: list[str] | None = None,
    campaign_type: str,
    retry_notes: str | None = None,
) -> tuple[str, int]:
    """`reference_kinds` lists which real images will be given directly to the image
    generator, one entry per image, in upload order — each "brand" or "product". Any
    number of each is supported (e.g. several guideline pages, several product photos).
    The prompt-writing instructions adapt to what's actually available."""
    reference_kinds = reference_kinds or []
    tool = {
        "name": "record_image_prompt",
        "description": "Record the image generation prompt for this message angle.",
        "input_schema": {
            "type": "object",
            "properties": {"image_prompt": {"type": "string"}},
            "required": ["image_prompt"],
        },
    }
    reference_instruction = _describe_references(reference_kinds, has_product_profile=bool(product_profile))

    system = (
        "You write image-generation prompts for social ad creative. The prompt must faithfully render "
        "the brand's color palette, mascot (if any), and visual style, and fit a "
        f"'{campaign_type}' campaign. Be visually specific — composition, subject, lighting, "
        f"color palette — not just a restatement of the message angle. {reference_instruction}"
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
# Step 2b (video): given the same image prompt, describe how the still should
# move — a separate small call, not folded into write_image_prompt, since a
# video variant needs both an image prompt (unchanged) and this in addition,
# and it's easy to review/edit the two independently before generation.
# ---------------------------------------------------------------------------
def ideate_motion_prompt(
    *,
    angle: str,
    image_prompt: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    campaign_type: str,
) -> tuple[str, int]:
    tool = {
        "name": "record_motion_prompt",
        "description": "Record the motion/animation prompt for this video variant.",
        "input_schema": {
            "type": "object",
            "properties": {"motion_prompt": {"type": "string"}},
            "required": ["motion_prompt"],
        },
    }
    system = (
        "You write short motion prompts for an image-to-video generator that will animate a still ad "
        "image. Describe camera movement (e.g. slow push-in, gentle pan, static with subject motion) "
        "and/or subject motion (e.g. product rotating, liquid pouring, mascot waving) — a few seconds "
        "of natural, brand-appropriate motion, not a scene change. Stay consistent with the brand's "
        f"style and a '{campaign_type}' campaign. Do not describe new elements not in the still image — "
        "the video starts from that exact image, only add motion."
    )
    user_content = (
        f"Brand profile: {brand_profile}\n\nMessage angle: {angle}\n\n"
        f"Starting image's generation prompt (this is what the still looks like): {image_prompt}"
    )
    if product_profile:
        user_content += f"\n\nProduct profile: {product_profile}"
    messages = [{"role": "user", "content": user_content}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool)
    return result["motion_prompt"], tokens


# ---------------------------------------------------------------------------
# Brand intake: pick one of OpenAI's 13 gpt-4o-mini-tts voices to represent this
# brand consistently across every video variant it ever generates — a real
# brand voice, not a random pick per ad. Called once, at brand creation.
# ---------------------------------------------------------------------------
def choose_brand_voice(brand_profile: dict[str, Any]) -> tuple[str, int]:
    from .openai_tts import VALID_VOICES  # local import avoids a cycle (openai_tts doesn't import llm, but keeps the voice list single-sourced)

    tool = {
        "name": "record_voice_choice",
        "description": "Record which voice best represents this brand.",
        "input_schema": {
            "type": "object",
            "properties": {"voice": {"type": "string", "enum": VALID_VOICES}},
            "required": ["voice"],
        },
    }
    system = (
        "You pick a text-to-speech voice for a brand's ad voiceovers, from a fixed list of options. Base "
        "the choice on the brand's tone/personality/style as described in its guideline — energetic vs "
        "calm, playful vs professional, warm vs bold. This voice will be reused across every ad this "
        "brand ever generates, so it needs to fit the brand generally, not any single campaign. Prefer "
        "'marin' or 'cedar' by default — OpenAI's newest, most natural-sounding and expressive voices for "
        "this model — unless another voice is a clearly better personality fit (e.g. 'onyx' for an "
        "authoritative/deep brand, 'shimmer' for a bright/cheerful one); don't default to an older voice "
        "like 'nova' or 'alloy' just because it's a recognizable name — they're flatter/less expressive."
    )
    messages = [{"role": "user", "content": f"Brand profile: {brand_profile}\n\nPick the best-fit voice."}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool, max_tokens=200)
    return result["voice"], tokens


# ---------------------------------------------------------------------------
# Step 2b (audio): a short spoken script + delivery direction + a music style
# description for one video variant — written together in one call since all
# three describe the same few seconds of audio and are easiest to keep
# consistent with each other that way. Budgeted to the video's real duration
# so the mix step (services/audio_mix.py) doesn't have to truncate mid-word.
# ---------------------------------------------------------------------------
def write_audio_script(
    *,
    angle: str,
    image_prompt: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    campaign_type: str,
    duration_seconds: float,
) -> tuple[dict[str, str], int]:
    tool = {
        "name": "record_audio_script",
        "description": "Record the voiceover script, delivery direction, and music prompt for this video variant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "voiceover_script": {
                    "type": "string",
                    "description": "The exact words to be spoken — short enough to comfortably fit the "
                    "given duration at a natural speaking pace (roughly 2.5 words/second). Punchy, "
                    "ad-native phrasing, not a restatement of the written social caption. Write real ad "
                    "copy about the brand/product/offer — do NOT narrate the message angle's underlying "
                    "concept as if reading its label out loud (angle 'chaos to calm' becoming the literal "
                    "line 'Chaos in. Calm out.' is the failure mode to avoid). If the angle has an "
                    "emotional arc, that arc belongs in voice_instructions as a delivery direction, not "
                    "spoken as the words themselves.",
                },
                "voice_instructions": {
                    "type": "string",
                    "description": "Plain-language delivery direction for a TTS model — tone, pace, "
                    "emotion (e.g. 'energetic and upbeat, quick pace' or 'calm, warm, reassuring'). Must "
                    "explicitly call for expressive, dynamic delivery — varied pitch and emphasis across "
                    "the line, not a flat/monotone/robotic reading. Naming specific words to stress or a "
                    "moment to land with more weight (e.g. 'emphasize \"free\" like it's the whole point') "
                    "gives the model something concrete to vary around, which matters even more for a "
                    "short script that has little room to build an arc on its own.",
                },
                "music_prompt": {
                    "type": "string",
                    "description": "A short instrumental music style description for a background bed "
                    "(e.g. 'upbeat minimal synth-pop, energetic' or 'soft acoustic guitar, warm'). Must "
                    "describe instrumental music only — never mention lyrics or words.",
                },
            },
            "required": ["voiceover_script", "voice_instructions", "music_prompt"],
        },
    }
    system = (
        "You write a short ad voiceover script, its delivery direction, and a background music style "
        f"description for a '{campaign_type}' video ad, roughly {duration_seconds:.0f} seconds long. "
        "Match the brand's tone and this specific message angle — but the angle is creative direction for "
        "you to work from, not text to transcribe. If the angle describes an emotional arc or before/after "
        "concept, express that through voice_instructions (a tone/pace shift during delivery) and through "
        "what the ad copy is actually about — never by having the voiceover literally speak the concept's "
        "own words (angle 'chaos to calm' → script 'Chaos in. Calm out.' is exactly the mistake to avoid). "
        "The script must fit the duration naturally at conversational pace — err short, not long; a "
        "truncated-mid-sentence voiceover is worse than a slightly short one. But don't over-compress into "
        "a string of clipped fragments just to save time — a short line with real sentence flow gives a "
        "TTS voice somewhere to put an emotional arc; deadpan fragments in a row read flat almost no "
        "matter how it's delivered, regardless of how expressive the voice_instructions are."
    )
    user_content = (
        f"Brand profile: {brand_profile}\n\nMessage angle: {angle}\n\n"
        f"The video's visual scene (for tonal consistency, not to be read aloud): {image_prompt}"
    )
    if product_profile:
        user_content += f"\n\nProduct profile: {product_profile}"
    messages = [{"role": "user", "content": user_content}]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool)
    return result, tokens


# ---------------------------------------------------------------------------
# Step 2c: the one real agent loop — vision-based brand-compliance check
# ---------------------------------------------------------------------------
def check_image_quality(
    *,
    image_bytes: bytes,
    media_type: str,
    brand_profile: dict[str, Any],
    product_profile: dict[str, Any] | None = None,
    reference_images: list[tuple[bytes, str]] | None = None,
    reference_kinds: list[str] | None = None,
) -> tuple[bool, str, int]:
    """Returns (passed, notes, output_tokens). `reference_images` (real photos actually
    given to the generator — brand guideline image and/or product photo, matching
    `reference_kinds` order) are shown alongside the generated image for a direct visual
    comparison; without them the check falls back to the text profiles only."""
    reference_images = reference_images or []
    reference_kinds = reference_kinds or []
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
        "image shows a different-looking product. If real reference photos are also shown (the brand's "
        "visual guideline and/or the actual product), compare the generated image directly against "
        "them (colors, mascot, product shape/proportions) rather than relying only on text."
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
    labels = {"brand": "brand visual guideline reference photo", "product": "real product reference photo"}
    for (ref_bytes, ref_media_type), kind in zip(reference_images, reference_kinds):
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
        text += f"{labels.get(kind, 'reference photo')} shown above. "
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
        "You write platform-native captions and hashtags for a social ad. Instagram: medium length "
        "— roughly 2-4 sentences, keyword-rich, SEO-style, NOT a long paragraph. TikTok: short, "
        "punchy caption with high-velocity hashtags. Facebook: can be slightly longer and more "
        "descriptive than Instagram. Match the brand's "
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
        "pre-computed verdicts (already-calculated stats and rankings, from real platform "
        "engagement data) — narrate them clearly, and never invent or adjust any number yourself.\n\n"
        "End with a '## Recommendation' section answering two things, grounded only in the "
        "verdicts you were given:\n"
        "1. Which variant, if any, is worth putting ad spend behind — based on how it performed "
        "relative to the *other* variants in this same campaign, not an absolute judgment. You "
        "have no external benchmark for what 'good' engagement looks like on any platform, so "
        "never claim a number is objectively high or low in isolation — only compare variants "
        "against each other.\n"
        "2. Which platform that variant should be boosted on, when its platform_breakdown shows "
        "a clear enough gap between platforms to say so — not a coin flip between two close numbers.\n\n"
        "You have no access to real ad costs, reach estimates, or Ads Manager data — never invent "
        "a specific ad budget, CPM, ROAS, or reach number; recommend *whether* and *where* to "
        "boost, not *how much* to spend. If the data doesn't support a clear call (only one "
        "variant has real data yet, or scores are too close to separate), say that plainly and "
        "recommend waiting for more data instead of forcing a recommendation."
    )
    messages = [
        {
            "role": "user",
            "content": f"Campaign type: {campaign_type}\n\nPre-computed verdicts: {verdicts}",
        }
    ]
    result, tokens = _forced_tool_call(system=system, messages=messages, tool=tool, max_tokens=1200)
    return result["summary_text"], tokens
