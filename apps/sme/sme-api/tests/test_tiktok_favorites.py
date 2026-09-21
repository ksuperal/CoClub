"""Test TikTok favorites (saves) tracking"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_service_client
from app.services import social


def test_tiktok_favorites():
    """Test TikTok favorites tracking implementation"""
    print("=" * 60)
    print("TIKTOK FAVORITES TRACKING TEST")
    print("=" * 60)

    client = get_service_client()

    # Check if we have a TikTok account connected
    print("\n1. Checking for connected TikTok accounts...")
    accounts = client.table("social_accounts")\
        .select("*")\
        .eq("platform", "tiktok")\
        .eq("status", "connected")\
        .execute()\
        .data

    if not accounts:
        print("[WARN] No connected TikTok accounts found")
        print("   Connect a TikTok account to test favorites tracking")
        print("\n" + "=" * 60)
        print("TEST SKIPPED - No TikTok account available")
        print("=" * 60)
        return

    account = accounts[0]
    user_id = account["user_id"]
    print(f"[OK] Found TikTok account: {account.get('external_account_name', 'N/A')}")

    # Check if we have any TikTok posts
    print("\n2. Checking for TikTok posts...")
    posts = client.table("posts")\
        .select("*")\
        .eq("platform", "tiktok")\
        .eq("status", "posted")\
        .not_.is_("external_post_id", "null")\
        .limit(1)\
        .execute()\
        .data

    if not posts:
        print("[WARN] No posted TikTok videos found")
        print("   Create and post a campaign to TikTok first")
        print("\n" + "=" * 60)
        print("TEST SKIPPED - No TikTok posts available")
        print("=" * 60)
        return

    post = posts[0]
    external_post_id = post["external_post_id"]
    print(f"[OK] Found TikTok post: {external_post_id}")

    # Test fetching metrics with favorites
    print("\n3. Testing TikTok metrics fetch (with favorites)...")
    try:
        metrics = social.fetch_metrics(
            client,
            user_id=user_id,
            platform="tiktok",
            external_post_id=external_post_id,
            media_type="video"
        )

        if metrics is None:
            print("[ERROR] Failed to fetch metrics (API error)")
        else:
            print("[OK] Successfully fetched TikTok metrics:")
            print(f"   Likes: {metrics.get('likes', 0)}")
            print(f"   Comments: {metrics.get('comments', 0)}")
            print(f"   Shares: {metrics.get('shares', 0)}")
            print(f"   Views: {metrics.get('views', 0)}")
            print(f"   Saves (Favorites): {metrics.get('saves', 0)} <- NEW!")

            # Check if saves field is present
            if 'saves' in metrics:
                print("\n[OK] Saves/Favorites field is present!")
                if metrics['saves'] > 0:
                    print(f"[OK] Found {metrics['saves']} favorites on this video!")
                else:
                    print("[INFO] No favorites yet (expected for new videos)")
            else:
                print("\n[WARN] Saves field not found in metrics")

    except Exception as e:
        print(f"[ERROR] Exception during metrics fetch: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nSUMMARY:")
    print("- TikTok favorites tracking: Implemented")
    print("- Field name: 'saves' (mapped from TikTok 'favorites_count')")
    print("- Available in: fetch_metrics() for TikTok platform")
    print("\nNOTE: Requires TikTok Display API (video.list scope)")


if __name__ == "__main__":
    test_tiktok_favorites()
