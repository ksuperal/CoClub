# CoClub UI Screens & Features Inventory

Complete list of all features and corresponding UI screens needed for CoClub.

---

## 🏠 1. ONBOARDING & AUTHENTICATION

### Screens Needed:
1. **Landing Page**
   - Hero section
   - Features overview
   - Pricing tiers (if applicable)
   - CTA: "Get Started"

2. **Sign Up**
   - Email/password form
   - OAuth options (Google, Facebook)
   - Terms acceptance

3. **Sign In**
   - Email/password form
   - "Forgot password" link
   - OAuth options

4. **Onboarding Wizard**
   - Step 1: Business type selection
   - Step 2: Connect social accounts (Facebook, Instagram, TikTok)
   - Step 3: Create first brand (optional)
   - Step 4: Tour/tutorial highlights

---

## 👤 2. DASHBOARD / HOME

### Main Dashboard Screen:
**Purpose:** Overview of all campaigns and quick actions

**Components:**
- **Header**
  - Logo
  - Main navigation (Dashboard, Campaigns, Brands, Products, Analytics, Settings)
  - User menu (Profile, Settings, Logout)
  - Notifications bell

- **Quick Stats Cards**
  ```
  ┌─────────────┬─────────────┬─────────────┬─────────────┐
  │ 5           │ 12          │ 8           │ 2           │
  │ Active      │ Total       │ Published   │ Pending     │
  │ Campaigns   │ Campaigns   │ Posts       │ Approvals   │
  └─────────────┴─────────────┴─────────────┴─────────────┘
  ```

- **Connected Accounts Status**
  ```
  ┌──────────────────────────────────────┐
  │ Connected Accounts                    │
  ├──────────────────────────────────────┤
  │ [✓] Instagram (@yourbrand)           │
  │ [✓] Facebook (Your Page)             │
  │ [✗] TikTok (Not connected)           │
  │                                      │
  │ [+ Connect More Accounts]            │
  └──────────────────────────────────────┘
  ```

- **Recent Campaigns List**
  - Campaign name
  - Status badge (Draft, Generating, Awaiting Approval, Posted, Completed)
  - Created date
  - Quick actions (View, Edit, Delete)

- **AI Recommendations Widget** ⭐ NEW
  ```
  ┌──────────────────────────────────────┐
  │ 💡 AI Recommendations                │
  ├──────────────────────────────────────┤
  │ 2 posts ready to boost!              │
  │ • Post #2: High confidence           │
  │ • Post #4: Medium confidence         │
  │                                      │
  │ [View Recommendations]               │
  └──────────────────────────────────────┘
  ```

- **CTA Button**
  - "Create New Campaign" (large, prominent)

---

## 🏢 3. BRAND MANAGEMENT

### 3.1 Brand Library Screen
**Purpose:** View and manage all brands

**Features:**
- Grid/list view toggle
- Search brands
- Filter (active/archived)
- Sort options

**Brand Card:**
```
┌────────────────────────────┐
│ [Brand Logo/Icon]          │
│                            │
│ Brand Name                 │
│ Fashion & Apparel          │
│                            │
│ 3 Products | 8 Campaigns   │
│                            │
│ [View] [Edit] [Archive]    │
└────────────────────────────┘
```

**Actions:**
- [+ Create New Brand] button

### 3.2 Create Brand Screen
**Purpose:** Create a new brand profile

**Form Fields:**
- Brand name
- Description (optional)
- Industry/category dropdown
- Brand guideline text area
- Upload brand assets (logo, colors, fonts, examples)
  - Drag & drop zone
  - Support: PDF, JPG, PNG
  - Max 10 files

**AI Processing Indicator:**
```
┌──────────────────────────────────────┐
│ 🤖 AI Processing Brand Guidelines... │
│ [=========>          ] 60%           │
│                                      │
│ Extracting:                          │
│ ✓ Brand colors                       │
│ ✓ Typography rules                   │
│ ⏳ Voice & tone guidelines           │
│ ⏳ Do's and Don'ts                   │
└──────────────────────────────────────┘
```

**Actions:**
- [Cancel] [Create Brand]

### 3.3 Brand Detail/Edit Screen
**Purpose:** View and edit brand profile

**Tabs:**
- **Overview**
  - Brand info
  - Extracted profile (AI-generated)
  - Brand voice preview

- **Assets**
  - Uploaded files gallery
  - Download/delete options

- **Products**
  - List of products under this brand
  - [+ Add Product] button

- **Campaigns**
  - List of campaigns using this brand
  - Performance summary

- **Settings**
  - Edit brand name/description
  - Upload new assets
  - Archive brand

---

## 📦 4. PRODUCT MANAGEMENT

### 4.1 Product Library Screen
**Purpose:** View products across all brands

**Features:**
- Filter by brand
- Search products
- Grid/list view

**Product Card:**
```
┌────────────────────────────┐
│ [Product Image]            │
│                            │
│ Product Name               │
│ Brand: StockingCo          │
│                            │
│ 2 Campaigns                │
│                            │
│ [View] [Edit] [Delete]     │
└────────────────────────────┘
```

### 4.2 Create Product Screen
**Purpose:** Add product to a brand

**Form:**
- Select brand (dropdown)
- Product name
- Description (optional)
- Upload product assets (1-10 images)
  - Product photos
  - Packaging
  - In-use shots
  - Drag & drop zone

**AI Processing:**
```
┌──────────────────────────────────────┐
│ 🤖 AI Analyzing Product...           │
│                                      │
│ Extracted Features:                  │
│ • Category: Hosiery                  │
│ • Colors: Nude, Beige, Dark          │
│ • Key Features: Sheer, Comfortable   │
│ • Use Cases: Office, Formal events   │
└──────────────────────────────────────┘
```

---

## 🎯 5. CAMPAIGN CREATION & MANAGEMENT

### 5.1 Campaigns List Screen
**Purpose:** View all campaigns

**Filters:**
- Status (All, Draft, Active, Completed)
- Brand
- Date range
- Campaign type

**Campaign List Item:**
```
┌─────────────────────────────────────────────────────┐
│ Campaign: "Spring Collection Launch"                │
│ Brand: StockingCo | Type: Product Launch            │
│ Status: [Completed] | Created: 3 days ago           │
│                                                     │
│ 📊 5 posts | 15,420 impressions | 850 clicks       │
│                                                     │
│ 💡 AI Recommendation: 2 posts ready to boost       │
│                                                     │
│ [View Campaign] [View Report] [Archive]            │
└─────────────────────────────────────────────────────┘
```

### 5.2 Create Campaign Screen (Step 1: Campaign Brief)
**Purpose:** Start a new campaign

**Form:**
- Select brand (dropdown)
- Select product (optional, dropdown)
- Campaign type (dropdown)
  - Product Launch
  - Event Announcement
  - Promo/Offer
  - Brand Awareness
  - Other

**Structured Brief (Recommended):** ⭐ NEW
```
┌──────────────────────────────────────────────┐
│ Campaign Brief                               │
├──────────────────────────────────────────────┤
│ Objective                                    │
│ [What should this content achieve?]          │
│ ____________________________________________ │
│                                              │
│ Target Audience                              │
│ [Who do you want to reach?]                  │
│ ____________________________________________ │
│                                              │
│ Single-Minded Message                        │
│ [One key message to remember]                │
│ ____________________________________________ │
│                                              │
│ USP (Unique Selling Proposition)             │
│ [Key selling point and reason]               │
│ ____________________________________________ │
│                                              │
│ Reason to Believe                            │
│ [Evidence/proof for credibility]             │
│ ____________________________________________ │
│                                              │
│ Call to Action (CTA)                         │
│ [What should audience do?]                   │
│ ____________________________________________ │
│                                              │
│ Mandatory Information                        │
│ [Price, dates, logo, etc.]                   │
│ ____________________________________________ │
│                                              │
│ Reference/Mood                               │
│ [Examples, tone preference]                  │
│ ____________________________________________ │
│                                              │
│ Format Preference                            │
│ ○ 1:1 Square  ○ 4:5 Portrait  ○ 9:16 Story  │
│                                              │
│ Product URL (Optional)                       │
│ [Landing page with UTM tracking]             │
│ ____________________________________________ │
└──────────────────────────────────────────────┘
```

**OR Simple Brief (Fallback):**
```
Brief (Free text):
[Describe your campaign in a few sentences...]
_____________________________________________
_____________________________________________
```

**AI Detection Preview:** ⭐ NEW
```
┌──────────────────────────────────────┐
│ 🤖 AI Detection Preview              │
├──────────────────────────────────────┤
│ Campaign Type: Educational           │
│ Primary Metric: Saves                │
│ Secondary Metric: Shares             │
│                                      │
│ Expected Performance:                │
│ • Excellent: 800+ saves              │
│ • Good: 500+ saves                   │
│ • Average: 300+ saves                │
└──────────────────────────────────────┘
```

**Actions:**
- [Cancel] [Next: Define Scope]

### 5.3 Campaign Scoping Screen (Step 2: Conversation)
**Purpose:** Define campaign scope via conversational UI

**Chat Interface:**
```
┌──────────────────────────────────────────────┐
│ 🤖 AI: How many posts would you like?       │
│                                              │
│ 👤 You: I need 9 Instagram posts and        │
│         2 TikTok short videos                │
│                                              │
│ 🤖 AI: Great! I'll create:                  │
│     • 9 Instagram posts (images + captions) │
│     • 2 TikTok videos (video + captions)    │
│                                              │
│     Would you like voiceover or music?      │
│                                              │
│ [Yes, add voiceover] [No, just video]       │
└──────────────────────────────────────────────┘
```

**Scope Summary Box:**
```
┌──────────────────────────────────────┐
│ Campaign Scope                       │
├──────────────────────────────────────┤
│ Instagram: 9 posts (images)          │
│ TikTok: 2 posts (videos + voiceover)│
│                                      │
│ Total: 11 pieces of content          │
└──────────────────────────────────────┘
```

**Actions:**
- [Back] [Confirm & Generate Content]

### 5.4 Content Generation Loading Screen
**Purpose:** Show progress while AI generates variants

```
┌──────────────────────────────────────────────┐
│ 🤖 AI is creating your content...           │
│                                              │
│ [====================] 100%                  │
│                                              │
│ ✓ Analyzed brand guidelines                 │
│ ✓ Generated 11 message angles               │
│ ✓ Created 11 image prompts                  │
│ ✓ Generating visuals... (9/11)              │
│ ⏳ Writing captions...                       │
│                                              │
│ Estimated time: ~2 minutes                   │
└──────────────────────────────────────────────┘
```

### 5.5 Content Review & Edit Screen (Approval Stage)
**Purpose:** Review, edit, and approve generated content

**Layout:**
- **Sidebar (Left):** Variant list with thumbnails
- **Main Area (Center):** Selected variant preview
- **Details Panel (Right):** Edit controls

**Variant Grid View:**
```
┌─────┬─────┬─────┬─────┐
│ [1] │ [2] │ [3] │ [4] │  ← Click to view/edit
│ IMG │ IMG │ IMG │ IMG │
└─────┴─────┴─────┴─────┘
```

**Selected Variant Detail:**
```
┌──────────────────────────────────────────────┐
│ Variant #2                                   │
│ Message Angle: "Find your perfect shade"    │
├──────────────────────────────────────────────┤
│                                              │
│          [Generated Image]                   │
│                                              │
│ Image Prompt:                                │
│ "Woman comparing stocking shades..."         │
│                                              │
│ Target Platforms:                            │
│ [✓] Instagram  [ ] Facebook  [ ] TikTok     │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ Instagram Caption:                           │
│ [Edit caption text...]                       │
│ ___________________________________________  │
│ ___________________________________________  │
│                                              │
│ Hashtags:                                    │
│ #stockings #fashion #style                   │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ Facebook Caption:                            │
│ [Edit caption text...]                       │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ Reference Asset (Optional):                  │
│ [Upload similar image for consistency]       │
│                                              │
│ [Regenerate Image] [Edit Prompts]           │
└──────────────────────────────────────────────┘
```

**Bulk Actions:**
```
Select: [✓] Variant 1, 2, 3, 5, 7
[Approve Selected (5)] [Delete Selected]
```

**Bottom Bar:**
```
[Save Draft] [Approve All & Publish] [Generate More Variants]
```

### 5.6 Publishing Confirmation Screen
**Purpose:** Final review before publishing

```
┌──────────────────────────────────────────────┐
│ Ready to Publish                             │
├──────────────────────────────────────────────┤
│ You're about to publish:                     │
│                                              │
│ 5 variants across 2 platforms:               │
│ • Instagram: 3 posts                         │
│ • Facebook: 2 posts                          │
│                                              │
│ Publishing will happen immediately.          │
│                                              │
│ [Cancel] [Confirm & Publish]                │
└──────────────────────────────────────────────┘
```

**Publishing Progress:**
```
┌──────────────────────────────────────────────┐
│ Publishing...                                │
├──────────────────────────────────────────────┤
│ ✓ Instagram Post 1/3 - Published             │
│ ✓ Instagram Post 2/3 - Published             │
│ ⏳ Instagram Post 3/3 - Publishing...        │
│ ⏳ Facebook Post 1/2 - Waiting...            │
│ ⏳ Facebook Post 2/2 - Waiting...            │
└──────────────────────────────────────────────┘
```

### 5.7 Campaign Dashboard (Post-Publish)
**Purpose:** Monitor campaign performance

**Tabs:**
- **Overview**
- **Posts**
- **Analytics**
- **Report**
- **Boost** ⭐ NEW

**Overview Tab:**
```
┌──────────────────────────────────────────────┐
│ Campaign: "Spring Collection"                │
│ Status: Active (Posted 48 hours ago)         │
├──────────────────────────────────────────────┤
│                                              │
│ ┌──────────┬──────────┬──────────┬─────────┐│
│ │ 15,420   │ 12,300   │ 850      │ 450     ││
│ │ Impressions Reach   │ Clicks   │ Saves   ││
│ └──────────┴──────────┴──────────┴─────────┘│
│                                              │
│ Performance Tier: EXCELLENT ⭐⭐⭐          │
│                                              │
│ 💡 AI Insight: Educational post exceeded    │
│    expected saves by 180%                    │
│                                              │
│ [View Full Report]                           │
└──────────────────────────────────────────────┘
```

**Posts Tab:**
```
┌──────────────────────────────────────────────┐
│ Published Posts (5)                          │
├──────────────────────────────────────────────┤
│                                              │
│ Post #2 - Instagram                          │
│ [Image Thumbnail]                            │
│ Saves: 450 | Likes: 350 | Comments: 25      │
│ Performance: EXCELLENT ⭐⭐⭐                │
│                                              │
│ 🚀 AI Recommendation: Boost this post!      │
│ [View Details] [Boost Now]                  │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ Post #4 - Facebook                           │
│ [Image Thumbnail]                            │
│ Likes: 120 | Comments: 8 | Shares: 15       │
│ Performance: GOOD ⭐⭐                       │
│                                              │
│ [View Details]                               │
└──────────────────────────────────────────────┘
```

**Analytics Tab:**
```
┌──────────────────────────────────────────────┐
│ Performance Over Time                        │
├──────────────────────────────────────────────┤
│                                              │
│        [Line Graph: Impressions]             │
│   15k ┤       ╭─────                         │
│   10k ┤    ╭──╯                              │
│    5k ┤ ╭──╯                                 │
│     0 └─────────────────────                 │
│       0h   24h   48h   72h                   │
│                                              │
│ Filter: [All Posts ▼] [Instagram ▼]         │
│ Metric: [Impressions ▼]                     │
└──────────────────────────────────────────────┘
```

**Report Tab:**
```
┌──────────────────────────────────────────────┐
│ Campaign Report                              │
│ Generated: 3 days after publishing           │
├──────────────────────────────────────────────┤
│                                              │
│ 📊 Summary                                   │
│ [AI-generated narrative report text...]      │
│                                              │
│ Top Performer: Post #2 (450 saves)           │
│                                              │
│ What Worked Well:                            │
│ • Question hook engaged audience             │
│ • Visual comparison style resonated          │
│ • Educational tips added value               │
│                                              │
│ Recommendations:                             │
│ • Continue educational content format        │
│ • Use product comparison visuals             │
│ • Lead with pain-point questions             │
│                                              │
│ [Download PDF Report]                        │
└──────────────────────────────────────────────┘
```

**Boost Tab:** ⭐ NEW
```
┌──────────────────────────────────────────────┐
│ 🎯 AI Boost Recommendations                 │
├──────────────────────────────────────────────┤
│                                              │
│ 2 posts ready to boost                       │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Post #2 - HIGH CONFIDENCE ⭐⭐⭐         │ │
│ │                                          │ │
│ │ Reason: Educational post exceeded        │ │
│ │ expected saves by 180% (450 vs 250)      │ │
│ │                                          │ │
│ │ AI Suggested Budget: $18/day for 7 days  │ │
│ │ Expected Reach: +25,000 people           │ │
│ │                                          │ │
│ │ [Boost Now] [Customize]                  │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Post #4 - MEDIUM CONFIDENCE ⭐⭐         │ │
│ │                                          │ │
│ │ Reason: Good engagement, moderate saves  │ │
│ │                                          │ │
│ │ AI Suggested Budget: $12/day for 5 days  │ │
│ │ Expected Reach: +15,000 people           │ │
│ │                                          │ │
│ │ [Boost Now] [Customize]                  │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Active Boosts: 0                             │
│ [View All Boosts]                            │
└──────────────────────────────────────────────┘
```

---

## 🚀 6. POST BOOSTING (NEW FEATURE)

### 6.1 Boost Configuration Modal
**Purpose:** Configure boost settings for a post

**Triggered by:** Clicking "Boost Now" on a post

```
┌──────────────────────────────────────────────┐
│ 🚀 Boost This Post                           │
├──────────────────────────────────────────────┤
│                                              │
│ [Post Thumbnail]                             │
│ "How to choose the right stocking shade"     │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ 💡 AI Recommendation                         │
│ "Educational post exceeded expected saves    │
│  by 180% - high potential for engagement"    │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ Ad Account                                   │
│ [My Business Ad Account ▼]                   │
│ Balance: $500.00 USD                         │
│                                              │
│ Budget Type                                  │
│ ● Daily Budget  ○ Lifetime Budget            │
│                                              │
│ Budget Amount                                │
│ $ [18.00] per day                            │
│   ↑ AI suggested                             │
│                                              │
│ Duration                                     │
│ [7] days                                     │
│  ↑ AI suggested                              │
│                                              │
│ Total Cost: $126.00                          │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ Campaign Objective                           │
│ [Engagement ▼]                               │
│ • Engagement (saves, likes, comments)        │
│ • Traffic (link clicks)                      │
│ • Awareness (reach)                          │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ Audience Targeting                           │
│ Location: [United States ▼]                  │
│ Age: [18] - [65]                             │
│ Gender: [All ▼]                              │
│                                              │
│ [⚙️ Advanced Targeting]                      │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ Expected Results                             │
│ • 📊 +25,000 people reached                  │
│ • ❤️ ~1,250 additional saves                │
│ • 💰 $2.85 CPM (per 1000 views)              │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ ⚠️ Payment Notice                            │
│ Meta will charge your ad account's payment   │
│ method directly. CoClub does not process     │
│ payment for ad spend.                        │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ [Cancel] [✅ Use AI Settings] [⚙️ Customize] │
│          [Start Boost - $126]                │
└──────────────────────────────────────────────┘
```

### 6.2 Active Boosts Dashboard
**Purpose:** Monitor all active and past boosts

**Navigation:** Settings > Boost Management OR Campaign > Boost Tab

```
┌──────────────────────────────────────────────┐
│ 🚀 Boost Management                          │
├──────────────────────────────────────────────┤
│                                              │
│ Tabs: [Active (2)] [Paused (1)] [Completed] │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ Active Boost #1                              │
│                                              │
│ [Post Thumbnail]                             │
│ Campaign: Spring Collection                  │
│ Post: "How to choose stocking shade"         │
│ Platform: Instagram                          │
│                                              │
│ Status: ACTIVE 🟢                            │
│ Started: 2 days ago | Ends: 5 days           │
│                                              │
│ Performance:                                 │
│ ┌──────────┬──────────┬──────────┬─────────┐│
│ │ 15,420   │ 12,300   │ 850      │ $45.67  ││
│ │Impressions Reach    │ Clicks   │ Spent   ││
│ └──────────┴──────────┴──────────┴─────────┘│
│                                              │
│ CPM: $2.96 | CPC: $0.054 | CTR: 5.51%       │
│                                              │
│ Budget: $18/day | Remaining: $80.33          │
│                                              │
│ [⏸️ Pause] [📊 View Metrics] [⚙️ Edit]      │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ Active Boost #2                              │
│ [Similar card...]                            │
└──────────────────────────────────────────────┘
```

### 6.3 Boost Performance Detail Screen
**Purpose:** Deep dive into boost metrics

```
┌──────────────────────────────────────────────┐
│ Boost Performance Detail                     │
│ Post: "How to choose stocking shade"         │
├──────────────────────────────────────────────┤
│                                              │
│ Status: ACTIVE 🟢                            │
│ Running: Day 3 of 7                          │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ Total Metrics                            │ │
│ ├──────────────────────────────────────────┤ │
│ │ Impressions: 15,420                      │ │
│ │ Reach: 12,300                            │ │
│ │ Clicks: 850                              │ │
│ │ Engagement: 1,200                        │ │
│ │ Conversions: 15                          │ │
│ │                                          │ │
│ │ Amount Spent: $45.67 / $126.00           │ │
│ │ CPM: $2.96                               │ │
│ │ CPC: $0.054                              │ │
│ │ CTR: 5.51%                               │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Performance Over Time                        │
│ [Line Graph: Impressions, Clicks, Spend]     │
│                                              │
│ Audience Demographics                        │
│ [Bar Chart: Age ranges]                      │
│ [Pie Chart: Gender split]                    │
│                                              │
│ [⏸️ Pause Boost] [🔄 Sync Metrics]           │
└──────────────────────────────────────────────┘
```

---

## 📊 7. ANALYTICS & INSIGHTS

### 7.1 Analytics Dashboard
**Purpose:** Overview of all content performance

**Filters:**
- Date range picker
- Platform filter
- Campaign filter
- Metric selector

```
┌──────────────────────────────────────────────┐
│ Analytics Overview                           │
├──────────────────────────────────────────────┤
│                                              │
│ Date Range: [Last 30 Days ▼]                │
│ Platform: [All Platforms ▼]                  │
│                                              │
│ ┌──────────┬──────────┬──────────┬─────────┐│
│ │ 125K     │ 98K      │ 5,200    │ 2,400   ││
│ │Total     │Total     │Total     │Total    ││
│ │Impressions Reach    │ Clicks   │ Saves   ││
│ │ +12%     │ +8%      │ +15%     │ +25%    ││
│ └──────────┴──────────┴──────────┴─────────┘│
│                                              │
│ Performance Trends                           │
│ [Multi-line Graph]                           │
│                                              │
│ Top Performing Posts                         │
│ 1. Post #12 - 850 saves (Educational)        │
│ 2. Post #8 - 620 saves (How-to)              │
│ 3. Post #5 - 450 clicks (Promotional)        │
│                                              │
│ Campaign Performance Comparison              │
│ [Bar Chart by campaign]                      │
└──────────────────────────────────────────────┘
```

### 7.2 Content Performance Insights
**Purpose:** AI-powered content analysis

**Navigation:** Analytics > Insights

```
┌──────────────────────────────────────────────┐
│ 💡 Content Performance Insights              │
├──────────────────────────────────────────────┤
│                                              │
│ What's Working Well                          │
│                                              │
│ ✓ Educational posts get 2.5x more saves      │
│ ✓ Question hooks increase engagement by 40%  │
│ ✓ Product comparison visuals perform best    │
│ ✓ Posts at 2pm get 30% more reach            │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ What Needs Improvement                       │
│                                              │
│ ✗ Promotional posts underperform on saves    │
│ ✗ Generic product shots get low engagement   │
│ ✗ Posts without CTAs have 60% fewer clicks   │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ AI Recommendations                           │
│                                              │
│ 1. Focus on educational content (how-to)     │
│ 2. Use question-based hooks consistently     │
│ 3. Add clear CTAs to all promotional posts   │
│ 4. Post during peak hours (2-4pm)            │
│                                              │
│ [View Detailed Analysis]                     │
└──────────────────────────────────────────────┘
```

### 7.3 Post Detail Analytics
**Purpose:** Deep dive into single post performance

```
┌──────────────────────────────────────────────┐
│ Post Performance Detail                      │
│ "How to choose the right stocking shade"     │
├──────────────────────────────────────────────┤
│                                              │
│ [Post Image/Video]                           │
│                                              │
│ Platform: Instagram | Posted: 5 days ago     │
│ Performance Tier: EXCELLENT ⭐⭐⭐          │
│                                              │
│ Metrics                                      │
│ ┌──────────┬──────────┬──────────┬─────────┐│
│ │ 8,500    │ 6,800    │ 450      │ 850     ││
│ │Impressions Reach    │ Saves    │ Likes   ││
│ └──────────┴──────────┴──────────┴─────────┘│
│                                              │
│ Performance vs Your Average                  │
│ • Saves: +180% ↑                             │
│ • Likes: +65% ↑                              │
│ • Comments: +40% ↑                           │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ 🤖 AI Analysis: What Made This Work          │
│                                              │
│ Hook Type: Question                          │
│ "Don't know which stocking color? 🤔"        │
│                                              │
│ Visual Style: Product Comparison             │
│ Side-by-side shade swatches resonated        │
│                                              │
│ Caption Strategy: Educational Tips           │
│ Step-by-step guide provided value            │
│                                              │
│ Why It Worked:                               │
│ "This post transformed a product promotion   │
│  into a practical reference tool. The        │
│  question hook validated shopper insecurity, │
│  then the visual comparison + step-by-step   │
│  tips gave actionable value users want to    │
│  save and share."                            │
│                                              │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                              │
│ 🚀 AI Recommendation                         │
│ This post is crushing it! Boost to reach     │
│ 25,000+ more people who will save & share.   │
│                                              │
│ Suggested: $18/day for 7 days                │
│                                              │
│ [Boost This Post]                            │
└──────────────────────────────────────────────┘
```

---

## ⚙️ 8. SETTINGS

### 8.1 Settings Main Screen
**Purpose:** Manage account and app settings

**Tabs:**
- **Profile**
- **Connected Accounts**
- **Ad Accounts** ⭐ NEW
- **Notifications**
- **Billing** (if applicable)
- **API Keys** (for developers)

### 8.2 Connected Accounts Tab
**Purpose:** Manage social media connections

```
┌──────────────────────────────────────────────┐
│ Connected Social Accounts                    │
├──────────────────────────────────────────────┤
│                                              │
│ Instagram                                    │
│ ┌──────────────────────────────────────────┐ │
│ │ ✓ Connected                              │ │
│ │ @yourbrand                               │ │
│ │ Instagram Business Account               │ │
│ │                                          │ │
│ │ Permissions: Post, Read Insights         │ │
│ │ Connected: 15 days ago                   │ │
│ │                                          │ │
│ │ [Disconnect] [Refresh Token]             │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ Facebook                                     │
│ ┌──────────────────────────────────────────┐ │
│ │ ✓ Connected                              │ │
│ │ Your Business Page                       │ │
│ │                                          │ │
│ │ Permissions: Manage Posts, Read Insights │ │
│ │ Connected: 15 days ago                   │ │
│ │                                          │ │
│ │ [Disconnect] [Refresh Token]             │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ TikTok                                       │
│ ┌──────────────────────────────────────────┐ │
│ │ ✗ Not Connected                          │ │
│ │                                          │ │
│ │ [Connect TikTok Account]                 │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

### 8.3 Ad Accounts Tab ⭐ NEW
**Purpose:** Manage Meta ad accounts for boosting

```
┌──────────────────────────────────────────────┐
│ Ad Accounts                                  │
├──────────────────────────────────────────────┤
│                                              │
│ Meta Ad Accounts                             │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ My Business Ad Account                   │ │
│ │ Account ID: act_123456789                │ │
│ │                                          │ │
│ │ Status: ACTIVE ●                         │ │
│ │ Currency: USD                            │ │
│ │ Balance: $500.00                         │ │
│ │ Spend Cap: $1,000/month                  │ │
│ │                                          │ │
│ │ Connected: 2 days ago                    │ │
│ │                                          │ │
│ │ [Disconnect] [Sync Balance]              │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ [+ Connect Another Ad Account]               │
│                                              │
│ ─────────────────────────────────────────    │
│                                              │
│ ℹ️ About Ad Accounts                         │
│                                              │
│ To boost posts, you need a Meta Ad Account   │
│ with an active payment method. Your card     │
│ will be charged directly by Meta for ad      │
│ spend - CoClub does not process payments.    │
│                                              │
│ [Learn More About Boosting]                  │
└──────────────────────────────────────────────┘
```

---

## 🔔 9. NOTIFICATIONS & ALERTS

### 9.1 Notifications Center
**Purpose:** View all notifications

**Triggered by:** Bell icon in header

```
┌──────────────────────────────────────────────┐
│ Notifications                                │
├──────────────────────────────────────────────┤
│                                              │
│ 🚀 2 posts recommended for boosting          │
│ Campaign: Spring Collection | 2 hours ago    │
│ [View Recommendations]                       │
│                                              │
│ ✓ Campaign completed                         │
│ Campaign: Spring Collection | 3 hours ago    │
│ [View Report]                                │
│                                              │
│ 📊 Your post is performing well!             │
│ Post #2 exceeded expected saves by 180%      │
│ 1 day ago | [View Post]                      │
│                                              │
│ ⚠️ Instagram token expiring soon             │
│ Reconnect by May 15 | 2 days ago             │
│ [Reconnect Now]                              │
│                                              │
│ [Mark All as Read]                           │
└──────────────────────────────────────────────┘
```

### 9.2 Notification Preferences
**Purpose:** Manage notification settings

**Location:** Settings > Notifications

```
┌──────────────────────────────────────────────┐
│ Notification Preferences                     │
├──────────────────────────────────────────────┤
│                                              │
│ Email Notifications                          │
│ [✓] Campaign completed                       │
│ [✓] Post published                           │
│ [✓] AI boost recommendations                 │
│ [✓] Performance milestones                   │
│ [ ] Weekly summary                           │
│                                              │
│ In-App Notifications                         │
│ [✓] All notifications                        │
│                                              │
│ Push Notifications (Mobile)                  │
│ [✓] Campaign updates                         │
│ [✓] Performance alerts                       │
│ [ ] Daily digest                             │
│                                              │
│ [Save Preferences]                           │
└──────────────────────────────────────────────┘
```

---

## 🎨 10. MEDIA LIBRARY (Optional Enhancement)

### Media Library Screen
**Purpose:** Centralized media asset management

```
┌──────────────────────────────────────────────┐
│ Media Library                                │
├──────────────────────────────────────────────┤
│                                              │
│ Filter: [All ▼] [Images] [Videos] [Brands]  │
│ Search: [________] [Upload New Media]        │
│                                              │
│ ┌──────┬──────┬──────┬──────┬──────┐        │
│ │ IMG  │ IMG  │ IMG  │ IMG  │ IMG  │        │
│ │      │      │      │      │      │        │
│ └──────┴──────┴──────┴──────┴──────┘        │
│                                              │
│ [Bulk Select] [Delete] [Download]            │
└──────────────────────────────────────────────┘
```

---

## 📱 11. MOBILE RESPONSIVE VIEWS

All screens should have mobile-optimized layouts:

### Mobile Navigation
- Hamburger menu
- Bottom tab bar (Dashboard, Campaigns, Analytics, Settings)
- Swipeable campaign cards

### Mobile Campaign Dashboard
- Stacked metrics cards
- Swipeable post gallery
- Simplified charts

---

## 🎯 SCREEN PRIORITY (MVP)

### Phase 1 - Core Functionality:
1. ✅ Landing Page
2. ✅ Sign Up/In
3. ✅ Dashboard
4. ✅ Brand Create/Edit
5. ✅ Product Create/Edit
6. ✅ Campaign Create (Brief)
7. ✅ Campaign Scoping
8. ✅ Content Review/Edit
9. ✅ Publishing Confirmation
10. ✅ Connected Accounts Settings

### Phase 2 - Analytics & Boost:
11. ⭐ Campaign Dashboard (Post-Publish)
12. ⭐ Post Detail Analytics
13. ⭐ Boost Configuration Modal
14. ⭐ Active Boosts Dashboard
15. ⭐ Ad Accounts Settings
16. ✅ Campaign Report View

### Phase 3 - Enhancement:
17. Analytics Dashboard
18. Content Performance Insights
19. Media Library
20. Notifications Center

---

## 📊 TOTAL SCREENS SUMMARY

**Authentication:** 4 screens
**Dashboard:** 1 screen
**Brand Management:** 3 screens
**Product Management:** 2 screens
**Campaign Management:** 7 screens
**Boost Features:** 3 screens ⭐ NEW
**Analytics:** 3 screens
**Settings:** 3 screens
**Notifications:** 2 screens
**Media Library:** 1 screen (optional)

**TOTAL: ~29 unique screens**

---

## 🎨 DESIGN SYSTEM NOTES

### Key Components Needed:
- **Cards** (Campaign card, Post card, Metric card)
- **Forms** (Multi-step, Single-page)
- **Modals** (Confirmation, Boost config, Edit)
- **Tables** (Campaign list, Post list)
- **Charts** (Line, Bar, Pie for analytics)
- **Status Badges** (Draft, Active, Completed, etc.)
- **Loading States** (Progress bars, Spinners)
- **Empty States** (No campaigns yet, No posts)
- **AI Recommendation Banners** ⭐
- **Metric Cards with Trends** ⭐

### Color Coding:
- **Success/Excellent:** Green
- **Good/Active:** Blue
- **Warning:** Yellow
- **Error/Poor:** Red
- **AI Features:** Purple/Gradient ⭐
- **Boost:** Orange/Gold ⭐

---

This is your complete UI screen inventory! Ready for wireframing. 🎨
