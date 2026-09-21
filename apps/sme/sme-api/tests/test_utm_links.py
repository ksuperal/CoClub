"""Test UTM link generation in captions"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "apps" / "sme" / "sme-api" / ".env"
load_dotenv(env_path)

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "sme" / "sme-api"))

from app.services import utm_tracking


def test_utm_link_generation():
    """Test UTM link generation for different platforms"""
    print("=" * 60)
    print("UTM LINK GENERATION TEST")
    print("=" * 60)

    base_url = "https://yourstore.com/product/nike-air-max"
    campaign_id = "abc-123-def-456"
    variant_id = "variant-xyz-789"

    print(f"\nBase URL: {base_url}")
    print(f"Campaign ID: {campaign_id}")
    print(f"Variant ID: {variant_id}\n")

    platforms = ["instagram", "facebook", "tiktok"]

    print("Generated UTM Links:")
    print("-" * 60)

    for platform in platforms:
        utm_link = utm_tracking.generate_utm_link(
            base_url=base_url,
            campaign_id=campaign_id,
            platform=platform,
            variant_id=variant_id,
        )
        print(f"\n{platform.upper()}:")
        print(f"  {utm_link}")

        # Extract and verify UTM parameters
        params = utm_tracking.extract_utm_params(utm_link)
        print(f"  UTM Source: {params['utm_source']}")
        print(f"  UTM Medium: {params['utm_medium']}")
        print(f"  UTM Campaign: {params['utm_campaign']}")
        print(f"  UTM Content: {params['utm_content']}")

        # Verify
        assert params['utm_source'] == platform, f"Expected {platform}, got {params['utm_source']}"
        assert params['utm_medium'] == "social", f"Expected social, got {params['utm_medium']}"
        assert params['utm_campaign'] == campaign_id, f"Expected {campaign_id}, got {params['utm_campaign']}"
        assert params['utm_content'] == variant_id, f"Expected {variant_id}, got {params['utm_content']}"

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)

    print("\n\nExample Caption with UTM Link:")
    print("-" * 60)
    caption = "New Nike Air Max just dropped!\n\nPerfect for your daily runs..."
    utm_link = utm_tracking.generate_utm_link(
        base_url=base_url,
        campaign_id=campaign_id,
        platform="instagram",
        variant_id=variant_id,
    )
    full_caption = f"{caption}\n\n[SHOP NOW] {utm_link}"
    print(full_caption)
    print("-" * 60)

    print("\n[OK] UTM link generation is working correctly!")
    print("[OK] Links will be automatically added to captions when product_url is provided")


if __name__ == "__main__":
    test_utm_link_generation()
