"""Test script for follower tracking functionality"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the API directory
env_path = Path(__file__).parent / "apps" / "sme" / "sme-api" / ".env"
load_dotenv(env_path)

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "sme" / "sme-api"))

from app.db import get_service_client
from app.services import follower_tracking


def test_follower_tracking():
    """Test follower tracking functionality"""
    print("=" * 60)
    print("FOLLOWER TRACKING TEST")
    print("=" * 60)

    client = get_service_client()

    # Test 1: Check if we have any social accounts connected
    print("\n1. Checking for connected social accounts...")
    accounts = client.table("social_accounts").select("*").execute().data

    if not accounts:
        print("[X] No social accounts found in database")
        print("   Connect a social account first to test follower tracking")
        return

    print(f"[OK] Found {len(accounts)} social account(s):")
    for acc in accounts:
        print(f"   - {acc['platform']}: {acc.get('external_account_name', 'N/A')}")
        print(f"     Current follower_count: {acc.get('follower_count', 'Not set')}")
        print(f"     Last updated: {acc.get('follower_count_updated_at', 'Never')}")

    # Test 2: Test the follower tracking service
    print("\n2. Testing follower tracking service...")

    for account in accounts:
        platform = account['platform']
        user_id = account['user_id']

        print(f"\n   Testing {platform} follower tracking...")

        try:
            # Test fetch_follower_count
            print(f"   - Fetching follower count from {platform} API...")
            count = follower_tracking.fetch_follower_count(
                client,
                user_id=user_id,
                platform=platform
            )

            if count is not None:
                print(f"   [OK] Successfully fetched: {count} followers")

                # Test update_follower_count
                print(f"   - Updating database...")
                success = follower_tracking.update_follower_count(
                    client,
                    user_id=user_id,
                    platform=platform
                )

                if success:
                    print(f"   [OK] Successfully updated database")

                    # Verify the update
                    updated = client.table("social_accounts")\
                        .select("follower_count, follower_count_updated_at")\
                        .eq("user_id", user_id)\
                        .eq("platform", platform)\
                        .single()\
                        .execute()\
                        .data

                    print(f"   [DATA] New follower_count: {updated['follower_count']}")
                    print(f"   [DATE] Updated at: {updated['follower_count_updated_at']}")
                else:
                    print(f"   [WARN] Update returned False")
            else:
                print(f"   [WARN] Could not fetch follower count (API may be unavailable or account not connected)")

        except Exception as e:
            print(f"   [ERROR] {e}")

    # Test 3: Test campaign follower growth calculation
    print("\n3. Testing campaign follower growth calculation...")

    campaigns = client.table("campaigns").select("id").limit(1).execute().data

    if not campaigns:
        print("   [INFO] No campaigns found to test with")
    else:
        campaign_id = campaigns[0]['id']

        print(f"   Testing with campaign ID: {campaign_id}")

        try:
            growth = follower_tracking.calculate_campaign_follower_growth(
                client,
                campaign_id=campaign_id
            )

            print(f"   [OK] Follower growth calculation result:")
            if growth:
                for platform, count in growth.items():
                    print(f"      {platform}: {count:+d} followers")
            else:
                print(f"      No growth data (campaign may not have posts yet)")

        except Exception as e:
            print(f"   [ERROR] {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_follower_tracking()
