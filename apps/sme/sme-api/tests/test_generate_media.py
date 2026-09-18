"""Phase 2 of the architecture migration: POST /campaigns/{id}/generate-media must
return immediately (variants marked 'generating', background job enqueued) instead of
blocking the request on the actual image/video generation loop. These tests cover only
that request-time contract -- the background job itself reuses the same
_generate_media_for_variant logic that already existed, just relocated -- so the actual
scheduling call is monkeypatched out rather than exercised for real.
"""

def _seed_campaign(fake_db, *, user_id: str, status: str = "awaiting_prompt_review") -> dict:
    return fake_db.seed(
        "campaigns",
        {
            "user_id": user_id,
            "brand_id": "brand-1",
            "product_id": None,
            "campaign_type": "product_launch",
            "brief": "Launch the thing",
            "status": status,
        },
    )


def _seed_variant(fake_db, *, campaign_id: str, media_type: str = "image") -> dict:
    return fake_db.seed(
        "variants",
        {
            "campaign_id": campaign_id,
            "message_angle": "Angle A",
            "image_prompt": "a product photo",
            "image_url": None,
            "quality_check_status": "pending",
            "quality_check_attempts": 0,
            "status": "pending",
            "media_type": media_type,
            "generation_status": "awaiting_prompt_review",
        },
    )


def test_generate_media_returns_immediately_with_generating_status(api_client, fake_db, login_as, monkeypatch):
    scheduled_calls = []
    monkeypatch.setattr(
        "app.pipeline.step2_variants.schedule_variant_media_generation",
        lambda campaign_id, user_id, variant_ids: scheduled_calls.append((campaign_id, user_id, variant_ids)),
    )

    campaign = _seed_campaign(fake_db, user_id="user-a")
    kept = _seed_variant(fake_db, campaign_id=campaign["id"])
    dropped = _seed_variant(fake_db, campaign_id=campaign["id"])

    login_as("user-a")
    resp = api_client.post(f"/v1/campaigns/{campaign['id']}/generate-media", json={"variant_ids": [kept["id"]]})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == kept["id"]
    assert body[0]["generation_status"] == "generating"

    # Deselected variant deleted, never generated.
    remaining_ids = {v["id"] for v in fake_db.store["variants"]}
    assert dropped["id"] not in remaining_ids

    # Campaign flipped into the in-progress status, and the background job was
    # handed off exactly once with the right args -- not actually run here.
    campaign_row = next(c for c in fake_db.store["campaigns"] if c["id"] == campaign["id"])
    assert campaign_row["status"] == "generating_variants"
    assert scheduled_calls == [(campaign["id"], "user-a", [kept["id"]])]


def test_generate_media_rejects_wrong_campaign_status(api_client, fake_db, login_as, monkeypatch):
    monkeypatch.setattr(
        "app.pipeline.step2_variants.schedule_variant_media_generation",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not be scheduled")),
    )

    campaign = _seed_campaign(fake_db, user_id="user-a", status="draft")
    variant = _seed_variant(fake_db, campaign_id=campaign["id"])

    login_as("user-a")
    resp = api_client.post(f"/v1/campaigns/{campaign['id']}/generate-media", json={"variant_ids": [variant["id"]]})

    assert resp.status_code == 409
