"""Regression coverage for two malformed shapes Claude's structured tool-use output
has actually returned live for `llm.write_captions` (confirmed via production logs,
not hypothetical): the whole captions array coming back as a JSON-encoded string, and
the array coming back double-wrapped under its own field name. Both used to crash
step3_copywriting.py (a cryptic "string indices must be integers" for the first) --
write_captions now normalizes both instead of failing.
"""

import pytest

from app.services import llm

GOOD_CAPTIONS = [
    {"platform": "instagram", "caption_text": "Hello!", "hashtags": ["#a"]},
    {"platform": "tiktok", "caption_text": "Hi!", "hashtags": ["#b"]},
]


def _patch_forced_tool_call(monkeypatch, tool_input: dict):
    monkeypatch.setattr(
        llm, "_forced_tool_call", lambda **kwargs: (tool_input, 42)
    )


def _call_write_captions():
    return llm.write_captions(
        message_angle="angle",
        brand_profile={},
        product_profile=None,
        campaign_type="product_launch",
        platforms=["instagram", "tiktok"],
    )


def test_normal_shape_passes_through(monkeypatch):
    _patch_forced_tool_call(monkeypatch, {"captions": GOOD_CAPTIONS})
    captions, tokens = _call_write_captions()
    assert captions == GOOD_CAPTIONS
    assert tokens == 42


def test_json_encoded_string_shape_is_recovered(monkeypatch):
    import json

    _patch_forced_tool_call(monkeypatch, {"captions": json.dumps(GOOD_CAPTIONS)})
    captions, _ = _call_write_captions()
    assert captions == GOOD_CAPTIONS


def test_double_wrapped_shape_is_recovered(monkeypatch):
    _patch_forced_tool_call(monkeypatch, {"captions": {"captions": GOOD_CAPTIONS}})
    captions, _ = _call_write_captions()
    assert captions == GOOD_CAPTIONS


def test_truly_malformed_shape_raises_clear_error(monkeypatch):
    _patch_forced_tool_call(monkeypatch, {"captions": {"not_captions": "garbage"}})
    with pytest.raises(RuntimeError, match="unexpected shape"):
        _call_write_captions()
