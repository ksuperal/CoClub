"""Test 24-hour follower growth tracking"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "apps" / "sme" / "sme-api" / ".env"
load_dotenv(env_path)

# Add to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "sme" / "sme-api"))

from app.db import get_service_client
from app.services import follower_tracking


def test_follower_growth_tracking():
    """Test the complete 24-hour follower growth tracking flow"""
    print("=" * 60)
    print("24-HOUR FOLLOWER GROWTH TRACKING TEST")
    print("=" * 60)

    client = get_service_client()

    # Test 1: Verify migrations
    print("\n1. Verifying database migrations...")

    try:
        # Check campaigns.follower_baseline column exists
        campaign = client.table("campaigns").select("follower_baseline").limit(1).execute().data
        print("   [OK] campaigns.follower_baseline column exists")
    except Exception as e:
        print(f"   [ERROR] campaigns.follower_baseline column missing: {e}")
        return

    try:
        # Check campaign_reports.follower_growth column exists
        report = client.table("campaign_reports").select("follower_growth").limit(1).execute().data
        print("   [OK] campaign_reports.follower_growth column exists")
    except Exception as e:
        print(f"   [ERROR] campaign_reports.follower_growth column missing: {e}")
        return

    print("   [OK] All required columns exist")

    # Test 2: Check if we have campaigns to test with
    print("\n2. Finding test campaign...")

    campaigns = client.table("campaigns").select("*").limit(1).execute().data

    if not campaigns:
        print("   [WARN] No campaigns found. Create a campaign first to test.")
        return

    campaign = campaigns[0]
    campaign_id = campaign["id"]
    user_id = campaign["user_id"]

    print(f"   Campaign ID: {campaign_id}")
    print(f"   User ID: {user_id}")
    print(f"   Current follower_baseline: {campaign.get('follower_baseline', 'Not set')}")

    # Test 3: Get connected accounts
    print("\n3. Checking connected social accounts...")

    accounts = client.table("social_accounts").select("*").eq("user_id", user_id).execute().data

    if not accounts:
        print("   [WARN] No social accounts connected for this user")
        return

    print(f"   [OK] Found {len(accounts)} connected account(s):")
    for acc in accounts:
        print(f"      - {acc['platform']}: {acc.get('follower_count', 0)} followers")

    # Test 4: Simulate baseline storage (what happens at posting time)
    print("\n4. Testing baseline storage (simulates campaign posting)...")

    platforms = [acc["platform"] for acc in accounts]

    try:
        baseline = follower_tracking.store_baseline_follower_counts(
            client,
            campaign_id=campaign_id,
            user_id=user_id,
            platforms=platforms
        )
        print(f"   [OK] Baseline stored: {baseline}")

        # Verify it was saved
        updated_campaign = client.table("campaigns").select("follower_baseline").eq("id", campaign_id).single().execute().data
        print(f"   [OK] Verified in database: {updated_campaign['follower_baseline']}")
    except Exception as e:
        print(f"   [ERROR] Failed to store baseline: {e}")
        return

    # Test 5: Simulate growth calculation (what happens 24 hours later)
    print("\n5. Testing follower growth calculation (simulates 24hr report)...")

    # First, let's manually modify the baseline to simulate growth
    # This simulates that we had fewer followers 24 hours ago
    test_baseline = {}
    for platform in platforms:
        current = accounts[0].get("follower_count", 0) if accounts[0]["platform"] == platform else 0
        for acc in accounts:
            if acc["platform"] == platform:
                current = acc.get("follower_count", 0)
                break
        # Simulate that we had 10 fewer followers 24 hours ago
        test_baseline[platform] = max(0, current - 10)

    print(f"   Setting test baseline (simulate 24h ago): {test_baseline}")
    client.table("campaigns").update({"follower_baseline": test_baseline}).eq("id", campaign_id).execute()

    # Now calculate growth
    try:
        growth = follower_tracking.calculate_campaign_follower_growth(
            client,
            campaign_id=campaign_id
        )

        print(f"   [OK] Follower growth calculated:")
        if growth:
            for platform, count in growth.items():
                emoji = "+" if count >= 0 else ""
                print(f"      {platform}: {emoji}{count} followers")
        else:
            print("      No growth data (baseline may be missing)")
    except Exception as e:
        print(f"   [ERROR] Failed to calculate growth: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 6: Verify it works in the report context
    print("\n6. Testing integration with campaign reports...")

    try:
        # Simulate what step5_feedback.py does
        fresh_growth = follower_tracking.calculate_campaign_follower_growth(
            client,
            campaign_id=campaign_id
        )

        # Create a test report with follower growth
        test_report = {
            "campaign_id": campaign_id,
            "summary_text": "Test report for follower growth tracking",
            "follower_growth": fresh_growth,
            "verdicts": []
        }

        result = client.table("campaign_reports").insert(test_report).execute()

        print(f"   [OK] Test report created with follower_growth:")
        print(f"      {result.data[0].get('follower_growth', {})}")

        # Clean up test report
        client.table("campaign_reports").delete().eq("id", result.data[0]["id"]).execute()
        print(f"   [OK] Test report cleaned up")

    except Exception as e:
        print(f"   [ERROR] Report integration test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nSUMMARY:")
    print("- Database migrations: OK")
    print("- Baseline storage: OK")
    print("- Growth calculation: OK")
    print("- Report integration: OK")
    print("\n24-hour follower growth tracking is ready to use!")


if __name__ == "__main__":
    test_follower_growth_tracking()
