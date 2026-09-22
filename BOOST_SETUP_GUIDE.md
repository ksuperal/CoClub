# Meta Post Boosting Setup Guide

This guide walks you through setting up Meta (Facebook/Instagram) post boosting functionality in CoClub.

## Overview

The post boosting feature allows CoClub users to:
- Connect their Meta Ad Accounts
- Boost high-performing posts programmatically
- Track ad performance and spend
- Pause/resume/manage boosts via API

## Prerequisites

### 1. Meta Developer Account & App
You already have a Meta app configured for OAuth (Facebook/Instagram login). You need to add **Marketing API** permissions to this app.

### 2. Meta Business Manager
Users need a **Meta Business Manager** account with:
- Connected Facebook Pages
- Connected Instagram Business Accounts
- At least one **Ad Account** with active payment method

---

## Step 1: Update Meta App Permissions

### 1.1 Request Additional Permissions

Go to your Meta App Dashboard at https://developers.facebook.com/apps/

Navigate to: **Your App > App Review > Permissions and Features**

Request the following permissions:

| Permission | Purpose | Access Level Needed |
|---|---|---|
| `ads_management` | Create, manage, delete ad campaigns | Standard Access |
| `ads_read` | Read ad performance data | Standard Access |
| `pages_manage_ads` | Boost posts from Facebook Pages | Standard Access |
| `pages_read_engagement` | Read Page engagement metrics | Standard Access |
| `pages_show_list` | List user's Pages | Standard Access |

### 1.2 App Review Process

For **Standard Access** (required for production):

1. **Click "Get Advanced Access"** for each permission
2. **Provide Use Case**:
   ```
   CoClub is a social media management platform that helps SMBs create and publish
   content to Facebook and Instagram. We need ads_management to allow users to boost
   high-performing posts directly from our platform, track ad spend, and monitor
   performance metrics.
   ```
3. **Submit Screencast Video** showing:
   - User connecting their Facebook/Instagram account
   - User selecting a post to boost
   - Boost configuration (budget, duration, targeting)
   - Boost creation and tracking
4. **Wait for Approval** (typically 3-7 business days)

### 1.3 Update OAuth Scopes

Update your Meta OAuth implementation to request these scopes:

**File**: `apps/sme/sme-api/app/services/meta_oauth.py`

Add to the `FACEBOOK_SCOPES` list:
```python
FACEBOOK_SCOPES = [
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "pages_manage_metadata",
    "instagram_basic",
    "instagram_content_publish",
    "instagram_manage_insights",
    # NEW: Add these for boosting
    "ads_management",
    "ads_read",
    "pages_manage_ads",
]
```

---

## Step 2: Link Meta App to Business Manager

### 2.1 Business Manager Setup

1. Go to **Meta Business Manager**: https://business.facebook.com/
2. Navigate to: **Business Settings > Apps > Add Apps**
3. **Add your Meta App** by App ID
4. **Assign Ad Accounts**:
   - Go to **Ad Accounts** section
   - Click **Assign Partners > Apps**
   - Select your app
   - Grant **"Advertise on behalf of this business"** permission

⚠️ **Critical**: Without this link, API calls will fail with "permission denied" even if OAuth scopes look correct.

### 2.2 Verify Access

Test if your app can access ad accounts:

```bash
curl "https://graph.facebook.com/v21.0/me/adaccounts?access_token=YOUR_ACCESS_TOKEN&fields=id,name"
```

You should see a list of ad accounts. If empty or error, review the Business Manager linkage.

---

## Step 3: Run Database Migration

Run the migration to create `ad_accounts` and `boosted_posts` tables:

```bash
# From project root
cd apps/sme/sme-api
supabase migration up
```

Or apply manually:
```bash
psql -U postgres -d coclub -f supabase/migrations/0025_add_boosted_posts_tracking.sql
```

---

## Step 4: User Flow - Connecting Ad Account

### 4.1 User Connects Facebook/Instagram (Existing Flow)
User already goes through OAuth to connect their Facebook Page and Instagram account.

### 4.2 NEW: Connect Ad Account

After connecting social accounts, users need to connect their ad account:

**Frontend Flow**:
```typescript
// 1. User clicks "Connect Ad Account" button
// 2. Call API to fetch and save ad accounts

const response = await fetch('/v1/boost/ad-accounts/connect', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ platform: 'facebook' })
});

const { accounts } = await response.json();
// accounts = [{ id, name, currency, balance, ... }]
```

**Backend** (already implemented):
- `POST /v1/boost/ad-accounts/connect`
- Fetches ad accounts from Meta API
- Saves to `ad_accounts` table

### 4.3 List Connected Ad Accounts

```typescript
const accounts = await fetch('/v1/boost/ad-accounts').then(r => r.json());
```

---

## Step 5: Boosting a Post

### 5.1 UI Implementation

Add a "Boost Post" button to posts that are:
- Status = "posted"
- Performance tier = "excellent" or "good"

**Frontend Example**:
```typescript
async function boostPost(postId: string, config: BoostConfig) {
  const response = await fetch(`/v1/boost/posts/${postId}/boost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ad_account_id: config.adAccountId,  // UUID from connected account
      objective: 'OUTCOME_ENGAGEMENT',    // or OUTCOME_TRAFFIC, OUTCOME_AWARENESS
      budget_amount: 10.00,                // $10/day
      budget_type: 'daily',                // or 'lifetime'
      duration_days: 7,                    // Run for 7 days
      targeting: {                         // Optional
        geo_locations: { countries: ['US'] },
        age_min: 18,
        age_max: 65
      }
    })
  });

  const result = await response.json();
  // result.boost = { id, external_campaign_id, status, ... }
}
```

### 5.2 Boost Objectives

| Objective | When to Use | Optimization Goal |
|---|---|---|
| `OUTCOME_ENGAGEMENT` | Educational content, high saves | `POST_ENGAGEMENT` |
| `OUTCOME_TRAFFIC` | Promotional, drive link clicks | `LINK_CLICKS` |
| `OUTCOME_AWARENESS` | Brand awareness, reach | `IMPRESSIONS` |

### 5.3 AI-Suggested Boosts (Future Enhancement)

The AI analytics system can automatically suggest which posts to boost:

```python
# In content_analysis.py or new boost_recommendations.py
def get_boost_recommendations(campaign_id: str) -> list[dict]:
    """Return posts that AI recommends boosting based on performance."""
    # Get posts that exceeded expected thresholds
    # Calculate potential ROI
    # Return sorted list with boost_reason
```

Example recommendation:
```json
{
  "post_id": "abc123",
  "boost_reason": "Educational post exceeded expected saves by 200% (1200 vs 60 expected)",
  "suggested_budget": 15.00,
  "estimated_additional_reach": 5000
}
```

---

## Step 6: Managing Boosts

### 6.1 View Active Boosts

**List all boosts for a post**:
```typescript
const boosts = await fetch(`/v1/boost/posts/${postId}/boosts`).then(r => r.json());
```

**List all boosts for a campaign**:
```typescript
const boosts = await fetch(`/v1/boost/campaigns/${campaignId}/boosts`).then(r => r.json());
```

### 6.2 Sync Metrics

Fetch latest performance metrics from Meta:
```typescript
await fetch(`/v1/boost/boosts/${boostId}/sync-metrics`, { method: 'POST' });
```

Boost record now contains:
```json
{
  "impressions": 15420,
  "reach": 12300,
  "clicks": 850,
  "engagement": 1200,
  "amount_spent": 45.67,
  "cpm": 2.96,
  "cpc": 0.054,
  "ctr": 5.51
}
```

### 6.3 Pause/Resume

```typescript
// Pause
await fetch(`/v1/boost/boosts/${boostId}/pause`, { method: 'POST' });

// Resume
await fetch(`/v1/boost/boosts/${boostId}/resume`, { method: 'POST' });
```

---

## Step 7: Monitoring & Metrics

### 7.1 Automated Metrics Sync (Recommended)

Add a background job to sync boost metrics every hour:

**Create**: `apps/sme/sme-api/app/jobs/sync_boost_metrics.py`

```python
"""Background job to sync boost metrics from Meta."""
def sync_all_active_boosts():
    client = get_service_client()

    # Get all active boosts
    boosts = client.table("boosted_posts").select("*").eq("status", "active").execute().data

    for boost in boosts:
        user_id = boost["user_id"]
        platform = boost["platform"]

        # Get access token
        account = client.table("social_accounts").select("access_token").eq("user_id", user_id).eq("platform", platform).single().execute().data

        if account and account.get("access_token"):
            try:
                meta_ads.sync_ad_metrics(
                    client,
                    boosted_post_id=boost["id"],
                    access_token=account["access_token"]
                )
            except Exception as e:
                logger.error(f"Failed to sync boost {boost['id']}: {e}")
```

Add to scheduler (e.g., using APScheduler or cron).

### 7.2 Dashboard Metrics

Display in UI:
- Total amount spent across all boosts
- Total impressions/reach gained
- Average CPM, CPC, CTR
- ROI calculation (compare organic vs boosted performance)

---

## Step 8: Important Notes & Limitations

### Rate Limits
- **Meta Marketing API**: 200 calls/hour per user
- **Meta Graph API**: 200 calls/hour per user + per app limits

### Minimum Budgets
- **Daily Budget**: $1.00 USD minimum
- **Lifetime Budget**: $1.00 USD minimum

### Ad Account Requirements
- Active payment method required
- Account must be verified
- Must pass Meta's ad policies

### Targeting Restrictions
- Some targeting options require special permissions
- Special ad categories (housing, employment, credit) have restricted targeting

### Token Expiry
- **User Access Tokens**: Expire after 60 days
- **Recommendation**: Implement token refresh flow
- Check token expiry before making ad API calls

### Cost Considerations
- You're spending the user's money from their ad account
- Implement **spend caps** and **budget alerts**
- Consider adding spend approval workflows

---

## Step 9: Testing

### 9.1 Test Mode Ads

Meta doesn't have a "sandbox" for ads, but you can:
- Use **very small budgets** ($1-2) for testing
- Set **short durations** (1-2 days)
- Target **specific locations** to limit reach
- Pause ads immediately after creation to test flow

### 9.2 Test Flow

1. **Connect ad account**: `POST /v1/boost/ad-accounts/connect`
2. **Create test post** (or use existing)
3. **Boost with $1 budget**: `POST /v1/boost/posts/{id}/boost`
4. **Verify campaign created** in Meta Ads Manager
5. **Sync metrics**: `POST /v1/boost/boosts/{id}/sync-metrics`
6. **Pause immediately**: `POST /v1/boost/boosts/{id}/pause`

---

## Step 10: Production Checklist

- [ ] Meta App has Standard Access for all required permissions
- [ ] Meta App is linked to Business Manager
- [ ] OAuth scopes updated to include ads permissions
- [ ] Database migration applied (0025)
- [ ] Frontend UI for "Boost Post" button
- [ ] Frontend UI for boost management (pause/resume/metrics)
- [ ] Background job for syncing boost metrics
- [ ] User education: "What is boosting?" tooltip/guide
- [ ] Budget safeguards: max spend limits, approval workflows
- [ ] Token refresh handling for long-running boosts
- [ ] Error handling for failed boosts (payment issues, policy violations)
- [ ] Analytics: Track boost ROI, compare organic vs paid performance

---

## API Reference

### Boost Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/v1/boost/ad-accounts` | GET | List connected ad accounts |
| `/v1/boost/ad-accounts/connect` | POST | Connect Meta ad accounts |
| `/v1/boost/posts/{post_id}/boost` | POST | Boost a post |
| `/v1/boost/posts/{post_id}/boosts` | GET | List all boosts for a post |
| `/v1/boost/campaigns/{campaign_id}/boosts` | GET | List all boosts for campaign |
| `/v1/boost/boosts/{id}/sync-metrics` | POST | Sync latest metrics |
| `/v1/boost/boosts/{id}/pause` | POST | Pause a boost |
| `/v1/boost/boosts/{id}/resume` | POST | Resume a boost |

---

## Troubleshooting

### "No ad accounts found"
- User needs to create an ad account in Meta Business Manager
- Add payment method to the ad account
- Link app to Business Manager

### "Permission denied" errors
- Verify app has Standard Access (not just default permissions)
- Check Business Manager > Apps > Your App has ad account access
- Ensure OAuth token has `ads_management` scope

### "Invalid post ID"
- Post must have `external_post_id` (set during publishing)
- Only posts with status="posted" can be boosted
- Instagram posts require Instagram Business account

### Boost creation fails
- Check ad account has sufficient balance/spend cap
- Verify payment method is active
- Check Meta ad policies (content may violate policies)
- Ensure budget meets minimum ($1 USD)

---

## Next Steps: TikTok Spark Ads

Once Meta boosting is stable, you can add TikTok Spark Ads following a similar pattern:
1. TikTok Marketing API access
2. TikTok Organic API for post selection
3. Similar database schema (already supports TikTok)
4. `services/tiktok_ads.py` implementation

---

## Resources

- [Meta Marketing API Docs](https://developers.facebook.com/docs/marketing-api/)
- [Boost Existing Post - Instagram Platform](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/partnership-ads/ads-creation/boost-existing-post/)
- [Meta Business Manager](https://business.facebook.com/)
- [Meta Ads API Setup Guide](https://admanage.ai/blog/meta-ads-api)

---

## Support

For issues with Meta Ads API integration, check:
1. Meta Developer Community Forums
2. Meta Business Help Center
3. Your Meta App's "Support Inbox" in developer dashboard

---

**Implementation Complete!** 🚀

You now have:
- ✅ Database schema for tracking boosts
- ✅ Meta Ads API service (`services/meta_ads.py`)
- ✅ Boost API endpoints (`routers/boost.py`)
- ✅ This comprehensive setup guide

Next: Follow Steps 1-3 to configure Meta app permissions and run the migration, then test the flow!
