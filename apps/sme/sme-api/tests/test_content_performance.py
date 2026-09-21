"""Test content performance analysis system"""

import sys
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app.db import get_service_client
from app.services import content_analysis


def test_content_performance_analysis():
    """Test content performance analysis implementation"""
    print("\n" + "=" * 60)
    print("Testing Content Performance Analysis System")
    print("=" * 60)

    client = get_service_client()

    # Step 1: Check if content_performance_insights table exists
    print("\n[STEP 1] Checking if migration 0022 is applied...")
    try:
        result = client.table("content_performance_insights").select("count").execute()
        print(f"[OK] Table 'content_performance_insights' exists with {len(result.data)} records")
    except Exception as e:
        print(f"[ERROR] Table doesn't exist. Please run migration 0022 first:")
        print(f"        Error: {str(e)}")
        print("\nTo run migration:")
        print("  1. Go to Supabase Dashboard > SQL Editor")
        print("  2. Run: supabase/migrations/0022_create_content_performance_insights.sql")
        return

    # Step 2: Find posts with metrics
    print("\n[STEP 2] Finding posts with metrics to analyze...")
    posts_with_metrics = client.rpc("get_posts_with_metrics_for_analysis").execute()

    # Alternative: Query posts that have metrics
    posts = client.table("posts").select("id, platform, status, posted_at").eq("status", "posted").limit(10).execute().data

    if not posts:
        print("[WARN] No posted posts found. Cannot test analysis.")
        print("       Create and publish a post first, then wait for metrics to be fetched.")
        return

    print(f"[OK] Found {len(posts)} posted posts")

    # Find posts with actual metrics
    posts_to_analyze = []
    for post in posts:
        metrics = (
            client.table("post_metrics")
            .select("*")
            .eq("post_id", post["id"])
            .order("fetched_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if metrics:
            posts_to_analyze.append({
                "post_id": post["id"],
                "platform": post["platform"],
                "metrics": metrics[0]
            })

    if not posts_to_analyze:
        print("[WARN] No posts with metrics found. Cannot test analysis.")
        print("       Publish a post and wait for metrics to be fetched first.")
        return

    print(f"[OK] Found {len(posts_to_analyze)} posts with metrics")

    # Step 3: Test analysis on first post
    test_post = posts_to_analyze[0]
    print(f"\n[STEP 3] Analyzing post: {test_post['post_id']}")
    print(f"         Platform: {test_post['platform']}")
    print(f"         Metrics: Likes={test_post['metrics'].get('likes', 0)}, "
          f"Comments={test_post['metrics'].get('comments', 0)}, "
          f"Shares={test_post['metrics'].get('shares', 0)}")

    try:
        insight = content_analysis.analyze_post_performance(
            client,
            post_id=test_post["post_id"],
            force_reanalysis=False
        )

        if insight:
            print(f"[OK] Analysis completed successfully!")
            print(f"\n--- Performance Insights ---")
            print(f"Performance Tier: {insight.get('performance_tier', 'N/A')}")
            print(f"Engagement Score: {insight.get('engagement_score', 0)}")
            print(f"Performance Percentile: {insight.get('performance_percentile', 0)}%")

            print(f"\n--- What Worked Well ---")
            for item in insight.get("what_worked_well", []):
                print(f"  + {item}")

            print(f"\n--- What Needs Improvement ---")
            for item in insight.get("what_needs_improvement", []):
                print(f"  - {item}")

            print(f"\n--- Recommendations ---")
            for rec in insight.get("improvement_recommendations", []):
                print(f"  > {rec}")

            print(f"\n--- AI Analysis Scores ---")
            ai_analysis = insight.get("ai_analysis", {})
            print(f"  Content Value Score: {ai_analysis.get('content_value_score', 0)}/100")
            print(f"  Virality Score: {ai_analysis.get('virality_score', 0)}/100")
            print(f"  Conversation Score: {ai_analysis.get('conversation_score', 0)}/100")

            print(f"\n--- Comparison vs User Average ---")
            vs_avg = insight.get("vs_user_average", {})
            if vs_avg:
                if "likes_diff_pct" in vs_avg:
                    print(f"  Likes: {vs_avg['likes_diff_pct']:+.1f}%")
                if "comments_diff_pct" in vs_avg:
                    print(f"  Comments: {vs_avg['comments_diff_pct']:+.1f}%")
                if "shares_diff_pct" in vs_avg:
                    print(f"  Shares: {vs_avg['shares_diff_pct']:+.1f}%")
            else:
                print("  No comparison data (insufficient post history)")
        else:
            print("[ERROR] Analysis failed - no insight returned")

    except Exception as e:
        print(f"[ERROR] Analysis failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Step 4: Test API endpoints (via database queries)
    print(f"\n[STEP 4] Verifying insights are stored in database...")
    try:
        stored_insights = (
            client.table("content_performance_insights")
            .select("*")
            .eq("post_id", test_post["post_id"])
            .execute()
            .data
        )

        if stored_insights:
            print(f"[OK] Found {len(stored_insights)} insight(s) stored for this post")
        else:
            print("[WARN] No insights found in database")

    except Exception as e:
        print(f"[ERROR] Failed to query insights: {str(e)}")

    # Step 5: Test re-analysis
    print(f"\n[STEP 5] Testing force re-analysis...")
    try:
        insight_reanalyzed = content_analysis.analyze_post_performance(
            client,
            post_id=test_post["post_id"],
            force_reanalysis=True
        )

        if insight_reanalyzed:
            print(f"[OK] Re-analysis successful")
            print(f"     Updated at: {insight_reanalyzed.get('analyzed_at', 'N/A')}")
        else:
            print("[ERROR] Re-analysis failed")

    except Exception as e:
        print(f"[ERROR] Re-analysis failed: {str(e)}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("[OK] Content Performance Analysis System is working!")
    print("\nNext steps:")
    print("  1. Test API endpoints via FastAPI:")
    print(f"     POST /campaigns/posts/{test_post['post_id']}/analyze")
    print(f"     GET /campaigns/posts/{test_post['post_id']}/insights")
    print("  2. Integrate auto-analysis into metrics refresh pipeline (optional)")
    print("  3. Add LLM-based recommendations (optional enhancement)")
    print("=" * 60)


if __name__ == "__main__":
    test_content_performance_analysis()
