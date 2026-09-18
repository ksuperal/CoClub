"""Regression coverage for the review's #1 security finding: RLS is bypassed by the
service-role key (`db.py`'s own docstring says isolation depends on every route
remembering to filter by user_id), and there was previously zero automated coverage
catching a missed filter. Each test seeds one user's data directly (bypassing the
create endpoints, which call out to the LLM/pipeline) and asserts a *different*
authenticated user gets 404 -- never the data -- from every read/write route that
takes a resource id.
"""


def _seed_brand(fake_db, *, user_id: str, name: str = "Acme") -> dict:
    return fake_db.seed(
        "brands",
        {
            "user_id": user_id,
            "name": name,
            "description": None,
            "extracted_profile": {},
            "voice_id": None,
            "brand_voice_id": None,
            "archived": False,
        },
    )


def _seed_campaign(fake_db, *, user_id: str, brand_id: str) -> dict:
    return fake_db.seed(
        "campaigns",
        {
            "user_id": user_id,
            "brand_id": brand_id,
            "product_id": None,
            "campaign_type": "product_launch",
            "brief": "Launch the thing",
            "variant_count": 3,
            "media_type": "image",
            "include_voiceover": False,
            "include_music": False,
            "scope_conversation": [],
            "content_plan": None,
            "status": "draft",
            "error_message": None,
            "warning_message": None,
            "updated_at": "2026-01-01T00:00:00+00:00",
        },
    )


def test_brand_not_visible_to_another_user(api_client, fake_db, login_as):
    brand = _seed_brand(fake_db, user_id="user-a")

    login_as("user-b")
    assert api_client.get(f"/v1/brands/{brand['id']}").status_code == 404
    assert (
        api_client.patch(f"/v1/brands/{brand['id']}", json={"name": "Hijacked"}).status_code
        == 404
    )
    assert api_client.delete(f"/v1/brands/{brand['id']}").status_code == 404

    login_as("user-a")
    owner_resp = api_client.get(f"/v1/brands/{brand['id']}")
    assert owner_resp.status_code == 200
    assert owner_resp.json()["name"] == "Acme"


def test_campaign_not_visible_to_another_user(api_client, fake_db, login_as):
    brand = _seed_brand(fake_db, user_id="user-a")
    campaign = _seed_campaign(fake_db, user_id="user-a", brand_id=brand["id"])

    login_as("user-b")
    assert api_client.get(f"/v1/campaigns/{campaign['id']}").status_code == 404

    login_as("user-a")
    owner_resp = api_client.get(f"/v1/campaigns/{campaign['id']}")
    assert owner_resp.status_code == 200
    assert owner_resp.json()["id"] == campaign["id"]


def test_brand_list_scoped_to_caller(api_client, fake_db, login_as):
    _seed_brand(fake_db, user_id="user-a", name="A's brand")
    _seed_brand(fake_db, user_id="user-b", name="B's brand")

    login_as("user-a")
    names = {b["name"] for b in api_client.get("/v1/brands").json()}
    assert names == {"A's brand"}
