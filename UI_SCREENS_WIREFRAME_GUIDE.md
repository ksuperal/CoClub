# CoClub UI Screens & Wireframe Guide

**Complete reference for wireframing all CoClub features**

Last Updated: 2026-09-22

---

## Table of Contents

1. [Authentication & Onboarding](#1-authentication--onboarding) (4 screens)
2. [Dashboard](#2-dashboard) (1 screen)
3. [Brand Management](#3-brand-management) (3 screens)
4. [Product Management](#4-product-management) (2 screens)
5. [Campaign Creation & Management](#5-campaign-creation--management) (7 screens)
6. [Post Boosting](#6-post-boosting) (3 screens) ⭐ NEW
7. [Analytics & Insights](#7-analytics--insights) (3 screens)
8. [Settings](#8-settings) (3 screens)
9. [Notifications](#9-notifications) (2 screens)
10. [Media Library](#10-media-library) (1 screen - optional)
11. [MVP Phase Prioritization](#mvp-phase-prioritization)
12. [Design System Guide](#design-system-guide)

**Total: 29 screens**

---

## 1. Authentication & Onboarding

### 1.1 Landing Page
**Route:** `/`
**Purpose:** Marketing page to attract new users

**Sections:**
- Hero section with value proposition
- Features overview (AI-powered content, multi-platform publishing, analytics)
- Pricing tiers (if applicable)
- Social proof / testimonials
- CTA: "Get Started" button

**Mobile:** Simplified hero, stacked features

---

### 1.2 Sign Up Screen
**Route:** `/signup`
**Purpose:** User registration

**Components:**
```
┌──────────────────────────────────────┐
│ Create Your CoClub Account           │
├──────────────────────────────────────┤
│                                      │
│ Email:    [____________________]     │
│ Password: [____________________]     │
│ Confirm:  [____________________]     │
│                                      │
│ [✓] I agree to Terms & Privacy      │
│                                      │
│ [Create Account]                     │
│                                      │
│ ─── OR ───                           │
│                                      │
│ [Continue with Google]               │
│ [Continue with Facebook]             │
│                                      │
│ Already have an account? [Sign In]   │
└──────────────────────────────────────┘
```

**Validation:**
- Email format check
- Password strength indicator
- Confirm password match

---

### 1.3 Sign In Screen
**Route:** `/login`
**Purpose:** User authentication

**Components:**
```
┌──────────────────────────────────────┐
│ Sign In to CoClub                    │
├──────────────────────────────────────┤
│                                      │
│ Email:    [____________________]     │
│ Password: [____________________]     │
│                                      │
│ [Remember me] [Forgot password?]     │
│                                      │
│ [Sign In]                            │
│                                      │
│ ─── OR ───                           │
│                                      │
│ [Continue with Google]               │
│ [Continue with Facebook]             │
│                                      │
│ Don't have an account? [Sign Up]     │
└──────────────────────────────────────┘
```

**Error Handling:**
- Invalid credentials message
- Rate limiting for failed attempts

---

### 1.4 Onboarding Wizard
**Route:** `/onboarding`
**Purpose:** First-time user setup
**Type:** Multi-step modal/full-page flow

**Step 1: Welcome**
```
┌──────────────────────────────────────┐
│ Welcome to CoClub! 👋                │
├──────────────────────────────────────┤
│                                      │
│ Let's set up your account in 3 steps│
│                                      │
│ [○ ○ ○]  Progress dots               │
│                                      │
│ What type of business are you?       │
│ ○ E-commerce                         │
│ ○ Service Provider                   │
│ ○ Agency                             │
│ ○ Other                              │
│                                      │
│ [Next]                               │
└──────────────────────────────────────┘
```

**Step 2: Connect Social Accounts**
```
┌──────────────────────────────────────┐
│ Connect Your Social Accounts         │
├──────────────────────────────────────┤
│                                      │
│ [● ○ ○]  Progress dots               │
│                                      │
│ Instagram                            │
│ [✓ Connected] @yourbrand             │
│                                      │
│ Facebook                             │
│ [Connect Facebook Page]              │
│                                      │
│ TikTok                               │
│ [Connect TikTok]                     │
│                                      │
│ [Skip for Now] [Next]                │
└──────────────────────────────────────┘
```

**Step 3: Create First Brand (Optional)**
```
┌──────────────────────────────────────┐
│ Create Your First Brand              │
├──────────────────────────────────────┤
│                                      │
│ [● ● ○]  Progress dots               │
│                                      │
│ Brand Name:                          │
│ [____________________]               │
│                                      │
│ Industry:                            │
│ [Fashion & Apparel ▼]                │
│                                      │
│ [Skip] [Create Brand & Get Started]  │
└──────────────────────────────────────┘
```

**Step 4: Tour (Optional)**
- Feature highlights overlay
- Interactive tooltips
- Skip tour option

---

## 2. Dashboard

### 2.1 Main Dashboard Screen
**Route:** `/dashboard`
**Purpose:** Home screen with overview and quick actions

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [Logo] Dashboard | Campaigns | Brands | Products | Settings │
│                                         [🔔] [👤 User Menu] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Quick Stats                                                 │
│ ┌──────────┬──────────┬──────────┬──────────┐              │
│ │ 5        │ 12       │ 8        │ 2        │              │
│ │ Active   │ Total    │ Published│ Pending  │              │
│ │ Campaigns│ Campaigns│ Posts    │ Approvals│              │
│ └──────────┴──────────┴──────────┴──────────┘              │
│                                                             │
│ ┌─────────────────────┬─────────────────────────────────┐  │
│ │ Connected Accounts  │ 💡 AI Recommendations           │  │
│ ├─────────────────────┼─────────────────────────────────┤  │
│ │ [✓] Instagram       │ 2 posts ready to boost!         │  │
│ │ [✓] Facebook        │ • Post #2: High confidence      │  │
│ │ [✗] TikTok          │ • Post #4: Medium confidence    │  │
│ │                     │                                 │  │
│ │ [+ Connect More]    │ [View Recommendations]          │  │
│ └─────────────────────┴─────────────────────────────────┘  │
│                                                             │
│ Recent Campaigns                                            │
│ ┌─────────────────────────────────────────────────────┐    │
│ │ Spring Collection Launch                            │    │
│ │ [Completed] | 3 days ago                            │    │
│ │ 💡 2 posts recommended for boost                    │    │
│ │ [View] [Report] [Archive]                           │    │
│ ├─────────────────────────────────────────────────────┤    │
│ │ Summer Sale Promo                                   │    │
│ │ [Active] | Posted 1 day ago                         │    │
│ │ [View Campaign]                                     │    │
│ └─────────────────────────────────────────────────────┘    │
│                                                             │
│ [➕ Create New Campaign] (Large CTA button)                │
└─────────────────────────────────────────────────────────────┘
```

**Key Actions:**
- Create new campaign
- View campaign details
- View boost recommendations
- Connect social accounts

---

## 3. Brand Management

### 3.1 Brand Library Screen
**Route:** `/brands`
**Purpose:** View and manage all brands

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Brands                                      [+ Create Brand] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [🔍 Search] [All Brands ▼] [Grid ⚏] [List ☰]              │
│                                                             │
│ ┌────────────┬────────────┬────────────┬────────────┐      │
│ │ [Logo]     │ [Logo]     │ [Logo]     │ [Logo]     │      │
│ │            │            │            │            │      │
│ │ Brand A    │ Brand B    │ Brand C    │ Brand D    │      │
│ │ Fashion    │ Beauty     │ Tech       │ Food       │      │
│ │            │            │            │            │      │
│ │ 3 Products │ 5 Products │ 1 Product  │ 8 Products │      │
│ │ 8 Campaigns│ 12 Camp.   │ 2 Camp.    │ 15 Camp.   │      │
│ │            │            │            │            │      │
│ │ [View]     │ [View]     │ [View]     │ [View]     │      │
│ │ [Edit]     │ [Edit]     │ [Edit]     │ [Edit]     │      │
│ └────────────┴────────────┴────────────┴────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Grid/list view toggle
- Search brands by name
- Filter: Active, Archived
- Sort: Name, Date created, # campaigns

---

### 3.2 Create Brand Screen
**Route:** `/brands/create`
**Purpose:** Create new brand profile with AI extraction

**Form:**
```
┌─────────────────────────────────────────────────────────────┐
│ Create New Brand                                   [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Brand Name *                                                │
│ [_____________________________________]                     │
│                                                             │
│ Description (Optional)                                      │
│ [_____________________________________]                     │
│ [_____________________________________]                     │
│                                                             │
│ Industry *                                                  │
│ [Fashion & Apparel ▼]                                       │
│                                                             │
│ Brand Guidelines (Optional)                                 │
│ [_____________________________________]                     │
│ [_____________________________________]                     │
│ [_____________________________________]                     │
│                                                             │
│ Upload Brand Assets (Logo, Colors, Examples)               │
│ ┌───────────────────────────────────────────────┐          │
│ │  📁 Drag & drop files here                    │          │
│ │     or click to browse                        │          │
│ │                                               │          │
│ │  Supported: PDF, JPG, PNG | Max 10 files      │          │
│ └───────────────────────────────────────────────┘          │
│                                                             │
│ Uploaded Files:                                             │
│ ✓ brand-guidelines.pdf (2.4 MB) [✕]                        │
│ ✓ logo-primary.png (580 KB) [✕]                            │
│                                                             │
│ [Cancel] [Create Brand]                                     │
└─────────────────────────────────────────────────────────────┘
```

**AI Processing State:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 AI Processing Brand Guidelines...                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [========════════>          ] 65%                           │
│                                                             │
│ Extracting brand profile:                                   │
│ ✓ Brand colors identified                                   │
│ ✓ Typography rules extracted                                │
│ ✓ Logo usage guidelines                                     │
│ ⏳ Voice & tone analysis in progress...                     │
│ ⏳ Do's and Don'ts extraction pending                       │
│                                                             │
│ Estimated time: ~1 minute                                   │
└─────────────────────────────────────────────────────────────┘
```

**Validation:**
- Brand name required
- Industry required
- At least 1 file uploaded recommended

---

### 3.3 Brand Detail/Edit Screen
**Route:** `/brands/:id`
**Purpose:** View and manage brand details

**Tabs:**
- Overview
- Assets
- Products
- Campaigns
- Settings

**Overview Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Brand A                                          [Edit Info] │
├─────────────────────────────────────────────────────────────┤
│ [Overview] Assets | Products | Campaigns | Settings         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Basic Info                                                  │
│ Industry: Fashion & Apparel                                 │
│ Created: 2 months ago                                       │
│ Last updated: 1 week ago                                    │
│                                                             │
│ AI-Extracted Brand Profile                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Brand Voice: Professional, aspirational, inclusive      │ │
│ │                                                         │ │
│ │ Color Palette:                                          │ │
│ │ [#000000] [#FFFFFF] [#C8A882] [#8B7355]                │ │
│ │                                                         │ │
│ │ Typography:                                             │ │
│ │ Headers: Playfair Display                               │ │
│ │ Body: Open Sans                                         │ │
│ │                                                         │ │
│ │ Key Guidelines:                                         │ │
│ │ • Always use inclusive language                         │ │
│ │ • Focus on empowerment and confidence                   │ │
│ │ • Avoid overly technical jargon                         │ │
│ │                                                         │ │
│ │ Do's:                                                   │ │
│ │ ✓ Use lifestyle imagery                                 │ │
│ │ ✓ Show product in context                               │ │
│ │                                                         │ │
│ │ Don'ts:                                                 │ │
│ │ ✗ Use generic stock photos                              │ │
│ │ ✗ Overcomplicate messaging                              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Quick Stats                                                 │
│ Total Products: 3                                           │
│ Total Campaigns: 8                                          │
│ Avg. Campaign Performance: GOOD ⭐⭐                        │
└─────────────────────────────────────────────────────────────┘
```

**Assets Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Brand Assets                                 [+ Upload More] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┐        │
│ │ [PDF]   │ [IMG]   │ [IMG]   │ [IMG]   │ [IMG]   │        │
│ │         │         │         │         │         │        │
│ │ Brand   │ Logo    │ Product │ Style   │ Color   │        │
│ │ Guide   │ Primary │ Photo   │ Guide   │ Palette │        │
│ │         │         │         │         │         │        │
│ │ 2.4 MB  │ 580 KB  │ 1.2 MB  │ 3.1 MB  │ 245 KB  │        │
│ │         │         │         │         │         │        │
│ │ [↓] [✕] │ [↓] [✕] │ [↓] [✕] │ [↓] [✕] │ [↓] [✕] │        │
│ └─────────┴─────────┴─────────┴─────────┴─────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**Products Tab:**
- List of products under this brand
- [+ Add Product] button
- Quick stats per product

**Campaigns Tab:**
- List of campaigns using this brand
- Performance summary per campaign
- [+ Create Campaign] button

**Settings Tab:**
- Edit brand name/description
- Update industry
- Upload new assets
- Archive/Delete brand (with confirmation)

---

## 4. Product Management

### 4.1 Product Library Screen
**Route:** `/products`
**Purpose:** View and manage products across all brands

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Products                                   [+ Create Product] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [🔍 Search] [All Brands ▼] [Grid ⚏] [List ☰]              │
│                                                             │
│ ┌───────────┬───────────┬───────────┬───────────┐          │
│ │ [Image]   │ [Image]   │ [Image]   │ [Image]   │          │
│ │           │           │           │           │          │
│ │ Product A │ Product B │ Product C │ Product D │          │
│ │ Brand: A  │ Brand: A  │ Brand: B  │ Brand: C  │          │
│ │           │           │           │           │          │
│ │ 2 Camp.   │ 5 Camp.   │ 3 Camp.   │ 1 Camp.   │          │
│ │           │           │           │           │          │
│ │ [View]    │ [View]    │ [View]    │ [View]    │          │
│ │ [Edit]    │ [Edit]    │ [Edit]    │ [Edit]    │          │
│ │ [Delete]  │ [Delete]  │ [Delete]  │ [Delete]  │          │
│ └───────────┴───────────┴───────────┴───────────┘          │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Filter by brand
- Search by product name
- Grid/list view
- Sort by name, date, campaigns

---

### 4.2 Create Product Screen
**Route:** `/products/create`
**Purpose:** Add product with AI analysis

**Form:**
```
┌─────────────────────────────────────────────────────────────┐
│ Create New Product                                [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Select Brand *                                              │
│ [Brand A ▼]                                                 │
│                                                             │
│ Product Name *                                              │
│ [_____________________________________]                     │
│                                                             │
│ Description (Optional)                                      │
│ [_____________________________________]                     │
│ [_____________________________________]                     │
│                                                             │
│ Upload Product Assets (1-10 images)                        │
│ ┌───────────────────────────────────────────────┐          │
│ │  📁 Drag & drop product images here           │          │
│ │                                               │          │
│ │  Supported: JPG, PNG | Max 10 files           │          │
│ └───────────────────────────────────────────────┘          │
│                                                             │
│ Uploaded Images:                                            │
│ [Img1] [Img2] [Img3] [Img4]                                │
│                                                             │
│ [Cancel] [Create Product]                                   │
└─────────────────────────────────────────────────────────────┘
```

**AI Analysis State:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 AI Analyzing Product...                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Extracted Product Features:                                 │
│                                                             │
│ Category: Hosiery & Stockings                               │
│ Colors: Nude, Beige, Black, Dark                            │
│ Material: Sheer, Semi-opaque                                │
│ Key Features: Comfortable, Durable, Seamless                │
│ Use Cases: Office wear, Formal events, Everyday             │
│                                                             │
│ ✓ Analysis complete                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Campaign Creation & Management

### 5.1 Campaigns List Screen
**Route:** `/campaigns`
**Purpose:** View all campaigns with filters

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Campaigns                                 [+ Create Campaign] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [🔍 Search] [All Statuses ▼] [All Brands ▼] [Date Range ▼]│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Spring Collection Launch                                │ │
│ │ Brand: StockingCo | Type: Product Launch                │ │
│ │ Status: [Completed ●] | Created: 3 days ago             │ │
│ │                                                         │ │
│ │ 📊 5 posts | 15,420 impressions | 850 clicks           │ │
│ │ 💡 AI Recommendation: 2 posts ready to boost           │ │
│ │                                                         │ │
│ │ [View Campaign] [View Report] [Archive]                │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Summer Sale Promo                                       │ │
│ │ Brand: StockingCo | Type: Promotional                   │ │
│ │ Status: [Active ●] | Posted: 1 day ago                 │ │
│ │                                                         │ │
│ │ 📊 3 posts | 8,200 impressions | 320 clicks            │ │
│ │                                                         │ │
│ │ [View Campaign]                                         │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ Fall Collection Teaser                                  │ │
│ │ Brand: StockingCo | Type: Brand Awareness               │ │
│ │ Status: [Draft ○] | Created: 5 hours ago               │ │
│ │                                                         │ │
│ │ [Continue Editing]                                      │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Status Colors:**
- Draft: Gray ○
- Generating: Blue ◐
- Awaiting Approval: Yellow ◑
- Active: Green ●
- Completed: Purple ●

---

### 5.2 Create Campaign Screen - Step 1: Brief
**Route:** `/campaigns/create`
**Purpose:** Define campaign objective and brief

**Structured Brief (Recommended):**
```
┌─────────────────────────────────────────────────────────────┐
│ Create Campaign - Step 1: Brief                   [1 of 3] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Select Brand *                                              │
│ [StockingCo ▼]                                              │
│                                                             │
│ Select Product (Optional)                                   │
│ [Sheer Elegance Collection ▼]                               │
│                                                             │
│ Campaign Type *                                             │
│ [Product Launch ▼]                                          │
│ Options: Product Launch, Event, Promo, Brand Awareness, etc│
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Campaign Brief (Structured)                                 │
│                                                             │
│ Objective                                                   │
│ What should this content achieve?                           │
│ [_________________________________________________]         │
│                                                             │
│ Target Audience                                             │
│ Who do you want to reach?                                   │
│ [_________________________________________________]         │
│                                                             │
│ Single-Minded Message                                       │
│ One key message you want people to remember                 │
│ [_________________________________________________]         │
│                                                             │
│ USP (Unique Selling Proposition)                            │
│ Key selling point and reason why it's important             │
│ [_________________________________________________]         │
│                                                             │
│ Reason to Believe                                           │
│ Evidence or proof that supports your claim                  │
│ [_________________________________________________]         │
│                                                             │
│ Call to Action (CTA)                                        │
│ What should the audience do after seeing this?              │
│ [_________________________________________________]         │
│                                                             │
│ Mandatory Information                                       │
│ Price, dates, logo, disclaimers, etc.                       │
│ [_________________________________________________]         │
│                                                             │
│ Reference/Mood                                              │
│ Examples, tone preference, visual style                     │
│ [_________________________________________________]         │
│                                                             │
│ Format Preference                                           │
│ ○ 1:1 Square  ○ 4:5 Portrait  ○ 9:16 Story                 │
│                                                             │
│ Product URL (Optional)                                      │
│ Landing page URL with UTM tracking                          │
│ [_________________________________________________]         │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ [Cancel] [Next: Define Scope]                               │
└─────────────────────────────────────────────────────────────┘
```

**AI Detection Preview (Shows after brief filled):**
```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 AI Campaign Analysis                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Detected Type: Educational                                  │
│ Primary Metric: Saves                                       │
│ Secondary Metric: Shares                                    │
│                                                             │
│ Expected Performance (based on your audience):              │
│ • Excellent: 800+ saves                                     │
│ • Good: 500+ saves                                          │
│ • Average: 300+ saves                                       │
│                                                             │
│ AI will optimize content for maximum saves and shares.      │
└─────────────────────────────────────────────────────────────┘
```

**Alternative: Simple Brief (Fallback)**
```
Brief (Free Text)
Describe your campaign in a few sentences...
[___________________________________________________]
[___________________________________________________]
[___________________________________________________]
[___________________________________________________]
```

---

### 5.3 Campaign Scoping Screen - Step 2: Conversation
**Route:** `/campaigns/create/scope`
**Purpose:** Define what content to create via conversational UI

**Chat Interface:**
```
┌─────────────────────────────────────────────────────────────┐
│ Create Campaign - Step 2: Scope                   [2 of 3] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🤖 AI: How many posts would you like to create?            │
│                                                             │
│ 👤 You: I need 9 Instagram posts and 2 TikTok videos       │
│     ┌─────────────────────────────────────┐                │
│     │ [Type your message...            ] [↑] │              │
│     └─────────────────────────────────────┘                │
│                                                             │
│ 🤖 AI: Great! I'll create:                                 │
│     • 9 Instagram posts (images + captions)                 │
│     • 2 TikTok videos (video + captions)                    │
│                                                             │
│     Would you like to add voiceover or music to the videos? │
│                                                             │
│ 👤 You: Yes, add voiceover                                 │
│                                                             │
│ 🤖 AI: Perfect! Here's your campaign scope:                │
│     ┌─────────────────────────────────────────────┐        │
│     │ Campaign Scope Summary                      │        │
│     ├─────────────────────────────────────────────┤        │
│     │ Instagram: 9 posts (images + captions)      │        │
│     │ TikTok: 2 posts (videos + voiceover)        │        │
│     │                                             │        │
│     │ Total: 11 pieces of content                 │        │
│     │                                             │        │
│     │ Est. generation time: ~5 minutes            │        │
│     └─────────────────────────────────────────────┘        │
│                                                             │
│     [Edit Scope] [Confirm & Generate]                       │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ [Back] [Confirm & Generate Content]                         │
└─────────────────────────────────────────────────────────────┘
```

**Suggested Quick Actions:**
- "9 Instagram posts"
- "1 TikTok video"
- "Mix of photos and videos"

---

### 5.4 Content Generation Loading Screen
**Route:** `/campaigns/create/generating`
**Purpose:** Show AI generation progress

```
┌─────────────────────────────────────────────────────────────┐
│ Generating Your Content...                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│           🤖 AI is creating your content                    │
│                                                             │
│ [====================████████░░░░░░░░] 60%                  │
│                                                             │
│ Progress:                                                   │
│ ✓ Analyzed brand guidelines                                 │
│ ✓ Generated 11 message angles                               │
│ ✓ Created 11 content prompts                                │
│ ✓ Generated 7 visuals (9 Instagram + 2 TikTok)             │
│ ⏳ Generating remaining visuals... (8/11)                   │
│ ⏳ Writing platform-specific captions...                    │
│ ⏳ Adding voiceover to TikTok videos...                     │
│                                                             │
│ Estimated time remaining: ~2 minutes                        │
│                                                             │
│ ℹ️ You can leave this page. We'll notify you when ready.   │
└─────────────────────────────────────────────────────────────┘
```

**On Completion:**
- Show success message
- Redirect to content review screen
- Send notification

---

### 5.5 Content Review & Edit Screen
**Route:** `/campaigns/:id/review`
**Purpose:** Review, edit, and approve generated content

**Layout: 3-Column**
```
┌─────────────────────────────────────────────────────────────┐
│ Review Campaign Content                    [Save Draft] [✕] │
├─────┬───────────────────────────────────────────┬───────────┤
│ VAR.│            PREVIEW AREA                   │  EDIT     │
│ LIST│                                           │  PANEL    │
├─────┼───────────────────────────────────────────┼───────────┤
│ [1] │ Variant #2 Selected                       │ Message:  │
│ IMG │ Message: "Find your perfect shade"        │ [Edit...]│
│     │                                           │           │
│ [2] │ ┌─────────────────────────────────────┐   │ Target:   │
│ IMG │ │                                     │   │ [✓] Insta │
│ ✓   │ │                                     │   │ [ ] FB    │
│ [3] │ │     [Generated Image]               │   │ [ ] TikTok│
│ IMG │ │                                     │   │           │
│     │ │                                     │   │ Caption:  │
│ [4] │ └─────────────────────────────────────┘   │ [Edit...] │
│ IMG │                                           │ [......] │
│ ✓   │ Image Prompt:                             │ [......] │
│ [5] │ "Woman comparing stocking shades..."      │           │
│ IMG │                                           │ Hashtags: │
│     │ Target Platforms:                         │ #stockings│
│ [6] │ [✓] Instagram  [ ] Facebook  [ ] TikTok  │ #fashion  │
│ IMG │                                           │           │
│ ✓   │ ─────────────────────────────────────     │ [Regen    │
│ [7] │                                           │  Image]   │
│ IMG │ Instagram Caption:                        │ [Edit     │
│     │ Find your perfect stocking shade! 🌟     │  Prompts] │
│ [8] │ Not sure which color suits your tone?     │           │
│ IMG │ Here's the ultimate guide...              │ Ref Asset:│
│     │                                           │ [Upload]  │
│ [9] │ #stockings #fashion #style                │           │
│ VID │                                           │           │
│     │ [Regenerate Image] [Edit Caption]         │           │
├─────┼───────────────────────────────────────────┼───────────┤
│ Bulk│ Selected: 5 variants                      │           │
│ [✓ Select All] [Approve Selected] [Delete]     │           │
└─────┴───────────────────────────────────────────┴───────────┘
│ [Save Draft] [Approve All & Publish] [Generate More]        │
└─────────────────────────────────────────────────────────────┘
```

**Variant Actions:**
- Click variant to view/edit
- Checkbox to select for bulk actions
- Edit caption per platform
- Regenerate image
- Upload reference asset
- Approve/reject individual variants

**Bulk Actions:**
- Select all/none
- Approve selected
- Delete selected
- Assign platforms

---

### 5.6 Publishing Confirmation Screen
**Route:** `/campaigns/:id/publish`
**Purpose:** Final review before publishing to social platforms

**Confirmation Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│ Ready to Publish                                  [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ You're about to publish:                                    │
│                                                             │
│ 5 approved variants across 2 platforms:                    │
│ • Instagram: 3 posts                                        │
│ • Facebook: 2 posts                                         │
│                                                             │
│ ⚠️ Publishing will happen immediately.                      │
│    Posts cannot be edited after publishing.                 │
│                                                             │
│ Connected Accounts:                                         │
│ ✓ Instagram: @yourbrand                                     │
│ ✓ Facebook: Your Business Page                              │
│                                                             │
│ [Cancel] [Confirm & Publish]                                │
└─────────────────────────────────────────────────────────────┘
```

**Publishing Progress:**
```
┌─────────────────────────────────────────────────────────────┐
│ Publishing...                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ✓ Instagram Post 1/3 - Published                            │
│   Posted at 2:15 PM                                         │
│                                                             │
│ ✓ Instagram Post 2/3 - Published                            │
│   Posted at 2:16 PM                                         │
│                                                             │
│ ⏳ Instagram Post 3/3 - Publishing...                       │
│                                                             │
│ ⏳ Facebook Post 1/2 - Waiting...                           │
│                                                             │
│ ⏳ Facebook Post 2/2 - Waiting...                           │
│                                                             │
│ [Cancel Remaining]                                          │
└─────────────────────────────────────────────────────────────┘
```

**On Completion:**
```
┌─────────────────────────────────────────────────────────────┐
│ ✓ Publishing Complete!                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ All 5 posts have been published successfully!               │
│                                                             │
│ • Instagram: 3 posts ✓                                      │
│ • Facebook: 2 posts ✓                                       │
│                                                             │
│ Metrics will be collected over the next 72 hours.           │
│ We'll notify you when the campaign report is ready.         │
│                                                             │
│ [View Campaign Dashboard]                                   │
└─────────────────────────────────────────────────────────────┘
```

---

### 5.7 Campaign Dashboard (Post-Publish)
**Route:** `/campaigns/:id`
**Purpose:** Monitor campaign performance after publishing

**Tabs:**
- Overview
- Posts
- Analytics
- Report
- Boost ⭐ NEW

**Overview Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Campaign: Spring Collection Launch          [Archive] [⚙️]  │
├─────────────────────────────────────────────────────────────┤
│ [Overview] Posts | Analytics | Report | Boost               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Status: Completed (Posted 72 hours ago)                     │
│ Brand: StockingCo | Type: Educational                       │
│                                                             │
│ ┌──────────┬──────────┬──────────┬──────────┐              │
│ │ 15,420   │ 12,300   │ 850      │ 450      │              │
│ │Impressions Reach   │ Clicks   │ Saves    │              │
│ │  +12%    │  +8%     │  +15%    │  +180%   │              │
│ └──────────┴──────────┴──────────┴──────────┘              │
│                                                             │
│ Performance Tier: EXCELLENT ⭐⭐⭐                          │
│                                                             │
│ 💡 AI Insight:                                              │
│ "Your educational content exceeded expected saves by 180%. │
│  Question hooks and product comparisons resonated strongly  │
│  with your audience. Continue this format for future        │
│  campaigns."                                                │
│                                                             │
│ Top Performer: Post #2 (450 saves, 850 likes)               │
│ [View Post Details]                                         │
│                                                             │
│ [View Full Report] [Download PDF]                           │
└─────────────────────────────────────────────────────────────┘
```

**Posts Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Published Posts (5)                          [Sort: Best ▼] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Post #2 - Instagram                                     │ │
│ │ ┌─────────┐                                             │ │
│ │ │ [Image] │ "How to choose the right stocking shade"   │ │
│ │ └─────────┘                                             │ │
│ │                                                         │ │
│ │ Saves: 450 | Likes: 850 | Comments: 35 | Shares: 28    │ │
│ │ Performance: EXCELLENT ⭐⭐⭐                            │ │
│ │                                                         │ │
│ │ 🚀 AI Recommendation: This post is crushing it!        │ │
│ │    Boost to reach 25,000+ more people.                 │ │
│ │    Suggested: $18/day for 7 days                       │ │
│ │                                                         │ │
│ │ [View Details] [Boost Now]                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Post #4 - Facebook                                      │ │
│ │ ┌─────────┐                                             │ │
│ │ │ [Image] │ "Stockings 101: Complete guide"            │ │
│ │ └─────────┘                                             │ │
│ │                                                         │ │
│ │ Likes: 120 | Comments: 8 | Shares: 15                  │ │
│ │ Performance: GOOD ⭐⭐                                  │ │
│ │                                                         │ │
│ │ [View Details]                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Analytics Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Performance Over Time                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Metric: [Impressions ▼] Platform: [All ▼] Post: [All ▼]   │
│                                                             │
│        Impressions Over 72 Hours                            │
│   15k ┤                           ╭─────────                │
│   12k ┤                    ╭──────╯                         │
│    9k ┤              ╭─────╯                                │
│    6k ┤        ╭─────╯                                      │
│    3k ┤   ╭────╯                                            │
│     0 └───┴────┴────┴────┴────┴────┴────┴────              │
│       0h   12h   24h   36h   48h   60h   72h                │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Platform Breakdown                                          │
│ ┌─────────────────┬─────────────────┐                      │
│ │ Instagram       │ Facebook        │                      │
│ │ 12,800 impressions 2,620 impressions                     │
│ │ 450 saves       │ 15 shares       │                      │
│ │ 3 posts         │ 2 posts         │                      │
│ └─────────────────┴─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

**Report Tab:**
```
┌─────────────────────────────────────────────────────────────┐
│ Campaign Report                                             │
│ Generated: 3 days after publishing                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 📊 Executive Summary                                        │
│                                                             │
│ [AI-generated narrative report text explaining overall      │
│  performance, top insights, and recommendations...]         │
│                                                             │
│ Top Performer: Post #2 (450 saves, 850 likes)               │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 💡 What Worked Well                                         │
│ • Question hook engaged audience effectively                │
│ • Visual product comparison style resonated                 │
│ • Educational tips provided real value                      │
│ • Posted during peak engagement hours (2-4 PM)              │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 🎯 AI Recommendations for Next Campaign                    │
│ 1. Continue educational content format (how-to guides)      │
│ 2. Use product comparison visuals consistently             │
│ 3. Lead with pain-point questions in hooks                  │
│ 4. Post at 2-4 PM for maximum reach                        │
│ 5. Consider boosting top performer (Post #2)                │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ [Download PDF Report] [Share Report]                        │
└─────────────────────────────────────────────────────────────┘
```

**Boost Tab:** ⭐ NEW
```
┌─────────────────────────────────────────────────────────────┐
│ 🎯 AI Boost Recommendations                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 2 posts ready to boost                                      │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Post #2 - HIGH CONFIDENCE ⭐⭐⭐                         │ │
│ │                                                         │ │
│ │ ┌─────────┐                                             │ │
│ │ │ [Image] │ "How to choose stocking shade"              │ │
│ │ └─────────┘                                             │ │
│ │                                                         │ │
│ │ Reason: Educational post exceeded expected saves by     │ │
│ │ 180% (450 saves vs 250 expected)                        │ │
│ │                                                         │ │
│ │ AI Suggested Budget: $18/day for 7 days                │ │
│ │ Total Cost: $126                                        │ │
│ │ Expected Reach: +25,000 people                          │ │
│ │ Expected Additional Saves: ~1,250                       │ │
│ │                                                         │ │
│ │ [🚀 Boost Now] [⚙️ Customize]                           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Post #4 - MEDIUM CONFIDENCE ⭐⭐                         │ │
│ │                                                         │ │
│ │ ┌─────────┐                                             │ │
│ │ │ [Image] │ "Stockings 101 guide"                       │ │
│ │ └─────────┘                                             │ │
│ │                                                         │ │
│ │ Reason: Good engagement with moderate saves             │ │
│ │                                                         │ │
│ │ AI Suggested Budget: $12/day for 5 days                │ │
│ │ Total Cost: $60                                         │ │
│ │ Expected Reach: +15,000 people                          │ │
│ │                                                         │ │
│ │ [🚀 Boost Now] [⚙️ Customize]                           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Active Boosts: 0                                            │
│ [View All Boosts]                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Post Boosting

### 6.1 Boost Configuration Modal
**Route:** Modal triggered from campaign dashboard
**Purpose:** Configure and launch a boosted post ad

**Full Modal:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Boost This Post                                [✕ Close] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────┐                                                 │
│ │ [Image] │ "How to choose the right stocking shade"       │
│ └─────────┘                                                 │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 💡 AI Recommendation                                        │
│ "Educational post exceeded expected saves by 180% - high    │
│  potential for engagement and shares."                      │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Ad Account                                                  │
│ [My Business Ad Account ▼]                                  │
│ Balance: $500.00 USD | Status: Active ●                    │
│                                                             │
│ Budget Type                                                 │
│ ● Daily Budget    ○ Lifetime Budget                         │
│                                                             │
│ Budget Amount                                               │
│ $ [18.00] per day                                           │
│   ↑ AI suggested based on performance                      │
│                                                             │
│ Duration                                                    │
│ [7] days                                                    │
│  ↑ AI suggested for high confidence posts                  │
│                                                             │
│ Total Cost: $126.00                                         │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Campaign Objective                                          │
│ [Engagement ▼]                                              │
│ • Engagement (saves, likes, comments)                       │
│ • Traffic (link clicks to website)                          │
│ • Awareness (maximize reach)                                │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Audience Targeting                                          │
│ Location: [United States ▼]                                 │
│ Age: [18] - [65]                                            │
│ Gender: [All ▼]                                             │
│ Interests: Auto-detected from post content                  │
│                                                             │
│ [⚙️ Advanced Targeting] (Optional)                          │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Expected Results (Estimates)                                │
│ • 📊 Reach: +25,000 people                                  │
│ • ❤️ Engagement: ~1,250 additional saves                   │
│ • 💰 CPM: $2.85 (cost per 1000 impressions)                 │
│ • 📈 CTR: ~5-7% estimated click-through rate                │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ ⚠️ Payment Notice                                           │
│ Meta will charge your ad account's payment method directly. │
│ CoClub does not process or handle payment for ad spend.     │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ [Cancel]  [✅ Use AI Settings]  [⚙️ Customize Further]     │
│           [Start Boost - $126.00]                           │
└─────────────────────────────────────────────────────────────┘
```

**States:**
- Default: Shows AI-recommended settings
- Editing: User can modify budget, duration, targeting
- Loading: "Creating boost campaign..."
- Success: "Boost active! View performance"
- Error: Show error message with retry

---

### 6.2 Active Boosts Dashboard
**Route:** `/boosts` or Settings > Boost Management
**Purpose:** Monitor all active and past boost campaigns

**Tabs:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Boost Management                              [Refresh] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Active (2)] [Paused (1)] [Completed (3)] [All]            │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Active Boost #1                                             │
│                                                             │
│ ┌─────────┐                                                 │
│ │ [Image] │ "How to choose stocking shade"                 │
│ └─────────┘                                                 │
│ Campaign: Spring Collection                                 │
│ Platform: Instagram                                         │
│                                                             │
│ Status: ACTIVE 🟢                                           │
│ Started: 2 days ago | Ends in: 5 days                      │
│                                                             │
│ Performance:                                                │
│ ┌──────────┬──────────┬──────────┬──────────┐              │
│ │ 15,420   │ 12,300   │ 850      │ $45.67   │              │
│ │Impressions Reach   │ Clicks   │ Spent    │              │
│ └──────────┴──────────┴──────────┴──────────┘              │
│                                                             │
│ CPM: $2.96 | CPC: $0.054 | CTR: 5.51%                      │
│                                                             │
│ Budget: $18/day | Total Budget: $126 | Remaining: $80.33   │
│                                                             │
│ [⏸️ Pause] [📊 View Detailed Metrics] [⚙️ Edit Budget]     │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Active Boost #2                                             │
│ [Similar card structure...]                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Actions:**
- Pause/Resume boost
- View detailed metrics
- Edit budget (increase/decrease)
- Sync latest metrics from Meta
- End boost early

---

### 6.3 Boost Performance Detail Screen
**Route:** `/boosts/:id`
**Purpose:** Deep dive into single boost performance

```
┌─────────────────────────────────────────────────────────────┐
│ Boost Performance Detail                         [Back] [✕] │
│ Post: "How to choose the right stocking shade"              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Status: ACTIVE 🟢                                           │
│ Running: Day 3 of 7 | Started: Mar 15 | Ends: Mar 22      │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Total Performance Metrics                               │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │                                                         │ │
│ │ Impressions: 15,420                                     │ │
│ │ Reach: 12,300 unique people                             │ │
│ │ Clicks: 850                                             │ │
│ │ Engagement: 1,200 (saves, likes, comments)              │ │
│ │ Conversions: 15 (link clicks to product)                │ │
│ │                                                         │ │
│ │ Amount Spent: $45.67 / $126.00 (36%)                    │ │
│ │ CPM: $2.96 (cost per 1000 impressions)                  │ │
│ │ CPC: $0.054 (cost per click)                            │ │
│ │ CTR: 5.51% (click-through rate)                         │ │
│ │ Conversion Rate: 1.76%                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Performance Over Time                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Multi-line graph showing impressions, clicks, spend]   │ │
│ │                                                         │ │
│ │   Metric: [All ▼] Time Range: [All Time ▼]            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Audience Demographics                                       │
│ ┌──────────────────────┬──────────────────────────────────┐ │
│ │ Age Breakdown        │ Gender Split                     │ │
│ │ [Bar Chart]          │ [Pie Chart]                      │ │
│ │                      │ • Female: 78%                    │ │
│ │ 18-24: 15%           │ • Male: 20%                      │ │
│ │ 25-34: 42%           │ • Other: 2%                      │ │
│ │ 35-44: 28%           │                                  │ │
│ │ 45-54: 12%           │                                  │ │
│ │ 55+: 3%              │                                  │ │
│ └──────────────────────┴──────────────────────────────────┘ │
│                                                             │
│ Top Locations                                               │
│ 1. United States (65%)                                      │
│ 2. Canada (12%)                                             │
│ 3. United Kingdom (8%)                                      │
│                                                             │
│ [⏸️ Pause Boost] [🔄 Sync Latest Metrics] [📊 Export Data] │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Analytics & Insights

### 7.1 Analytics Dashboard
**Route:** `/analytics`
**Purpose:** Overall content performance across all campaigns

```
┌─────────────────────────────────────────────────────────────┐
│ Analytics Overview                              [Export PDF] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Date Range: [Last 30 Days ▼]                                │
│ Platform: [All Platforms ▼] Brand: [All Brands ▼]          │
│                                                             │
│ ┌──────────┬──────────┬──────────┬──────────┐              │
│ │ 125,000  │ 98,000   │ 5,200    │ 2,400    │              │
│ │ Total    │ Total    │ Total    │ Total    │              │
│ │Impressions Reach   │ Clicks   │ Saves    │              │
│ │ +12% ↑   │ +8% ↑    │ +15% ↑   │ +25% ↑   │              │
│ └──────────┴──────────┴──────────┴──────────┘              │
│                                                             │
│ Performance Trends (Last 30 Days)                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Multi-line graph: Impressions, Reach, Engagement]     │ │
│ │                                                         │ │
│ │ Metric: [Impressions ▼] Breakdown: [By Day ▼]         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Top Performing Posts                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Post #12 - 850 saves (Educational)                  │ │
│ │    Campaign: Spring Collection                          │ │
│ │    [View Post]                                          │ │
│ │                                                         │ │
│ │ 2. Post #8 - 620 saves (How-to)                        │ │
│ │    Campaign: Summer Tips                                │ │
│ │    [View Post]                                          │ │
│ │                                                         │ │
│ │ 3. Post #5 - 450 clicks (Promotional)                  │ │
│ │    Campaign: Sale Announcement                          │ │
│ │    [View Post]                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Campaign Performance Comparison                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Bar chart comparing campaigns]                         │ │
│ │                                                         │ │
│ │ Sort: [Impressions ▼]                                   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 7.2 Content Performance Insights
**Route:** `/analytics/insights`
**Purpose:** AI-powered analysis of what works/doesn't work

```
┌─────────────────────────────────────────────────────────────┐
│ 💡 Content Performance Insights              [Refresh Data] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Based on analysis of 45 posts over the last 90 days        │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ ✅ What's Working Well                                      │
│                                                             │
│ ✓ Educational posts get 2.5x more saves                     │
│   (850 avg vs 340 avg for other content types)              │
│                                                             │
│ ✓ Question hooks increase engagement by 40%                 │
│   Posts starting with questions: 1,200 avg engagement       │
│   Posts without questions: 850 avg engagement               │
│                                                             │
│ ✓ Product comparison visuals perform best                   │
│   Side-by-side comparisons: +65% saves vs single product    │
│                                                             │
│ ✓ Posts at 2-4 PM get 30% more reach                       │
│   Peak hours: 2-4 PM (avg 8,500 reach)                     │
│   Off-peak: Other times (avg 6,200 reach)                   │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ ⚠️ What Needs Improvement                                   │
│                                                             │
│ ✗ Promotional posts underperform on saves                   │
│   Sale announcements: 120 avg saves (65% below average)     │
│                                                             │
│ ✗ Generic product shots get low engagement                  │
│   Plain product photos: -45% engagement vs lifestyle shots  │
│                                                             │
│ ✗ Posts without CTAs have 60% fewer clicks                  │
│   No CTA: 85 avg clicks | With CTA: 220 avg clicks         │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 🎯 AI Recommendations for Future Campaigns                  │
│                                                             │
│ 1. Focus on educational content (how-to, tips, guides)      │
│    Your audience values learning over selling               │
│                                                             │
│ 2. Use question-based hooks consistently                    │
│    "Don't know which...?" performs 40% better               │
│                                                             │
│ 3. Add clear CTAs to all promotional posts                  │
│    "Shop now", "Learn more", "Get yours" drive action      │
│                                                             │
│ 4. Post during peak engagement hours (2-4 PM)               │
│    Schedule posts when your audience is most active         │
│                                                             │
│ 5. Use lifestyle imagery over product-only shots            │
│    Show products in context for better engagement           │
│                                                             │
│ [View Detailed Analysis] [Export Insights]                  │
└─────────────────────────────────────────────────────────────┘
```

---

### 7.3 Post Detail Analytics
**Route:** `/posts/:id/analytics`
**Purpose:** Deep dive into individual post performance

```
┌─────────────────────────────────────────────────────────────┐
│ Post Performance Detail                    [Back to Campaign] │
│ "How to choose the right stocking shade"                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────┐                                     │
│ │                     │                                     │
│ │   [Post Image]      │                                     │
│ │                     │                                     │
│ └─────────────────────┘                                     │
│                                                             │
│ Platform: Instagram | Posted: 5 days ago                    │
│ Campaign: Spring Collection                                 │
│ Performance Tier: EXCELLENT ⭐⭐⭐                          │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Metrics Summary                                             │
│ ┌──────────┬──────────┬──────────┬──────────┐              │
│ │ 8,500    │ 6,800    │ 450      │ 850      │              │
│ │Impressions Reach   │ Saves    │ Likes    │              │
│ └──────────┴──────────┴──────────┴──────────┘              │
│                                                             │
│ Comments: 35 | Shares: 28 | Engagement Rate: 15.2%          │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Performance vs Your Average                                 │
│ • Saves: +180% ↑ (450 vs 160 avg)                          │
│ • Likes: +65% ↑ (850 vs 515 avg)                           │
│ • Comments: +40% ↑ (35 vs 25 avg)                          │
│ • Engagement Rate: +85% ↑ (15.2% vs 8.2% avg)              │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 🤖 AI Analysis: What Made This Post Work                    │
│                                                             │
│ Hook Type: Question                                         │
│ "Don't know which stocking color suits you? 🤔"            │
│ → Validates audience pain point, creates curiosity          │
│                                                             │
│ Visual Style: Product Comparison                            │
│ Side-by-side shade swatches with skin tones                 │
│ → Clear, practical, immediately useful visual               │
│                                                             │
│ Caption Strategy: Educational Tips                          │
│ Step-by-step guide with actionable advice                   │
│ → Provides real value users want to save and share          │
│                                                             │
│ Why It Worked:                                              │
│ "This post transformed a product promotion into a practical │
│  reference tool. The question hook validated shopper        │
│  insecurity, then the visual comparison + step-by-step tips │
│  gave actionable value. This is the type of content people  │
│  save for later and share with friends."                    │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ 🚀 AI Boost Recommendation                                  │
│                                                             │
│ This post is crushing it! Boost to reach 25,000+ more       │
│ people who will save and share this valuable content.       │
│                                                             │
│ Confidence: HIGH ⭐⭐⭐                                      │
│ Suggested Budget: $18/day for 7 days                        │
│ Expected Reach: +25,000 people                              │
│ Estimated Additional Saves: ~1,250                          │
│                                                             │
│ [🚀 Boost This Post]                                        │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ [View Full Caption] [Export Metrics] [Share Post]           │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Settings

### 8.1 Settings Main Screen
**Route:** `/settings`
**Purpose:** Manage account and app settings

**Tabs:**
- Profile
- Connected Accounts
- Ad Accounts ⭐ NEW
- Notifications
- Billing (if applicable)
- API Keys (for developers)

---

### 8.2 Connected Accounts Tab
**Route:** `/settings/accounts`
**Purpose:** Manage social media connections

```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                                    │
├─────────────────────────────────────────────────────────────┤
│ Profile | [Connected Accounts] | Ad Accounts | Notifications│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Connected Social Media Accounts                             │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Instagram                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ✓ Connected 🟢                                          │ │
│ │                                                         │ │
│ │ Account: @yourbrand                                     │ │
│ │ Type: Instagram Business Account                        │ │
│ │                                                         │ │
│ │ Permissions:                                            │ │
│ │ • Publish posts                                         │ │
│ │ • Read insights and metrics                             │ │
│ │ • Manage comments                                       │ │
│ │                                                         │ │
│ │ Connected: 15 days ago                                  │ │
│ │ Last activity: 2 hours ago                              │ │
│ │                                                         │ │
│ │ [Disconnect] [Refresh Token] [View Permissions]         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Facebook                                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ✓ Connected 🟢                                          │ │
│ │                                                         │ │
│ │ Page: Your Business Page                                │ │
│ │ Page ID: 123456789                                      │ │
│ │                                                         │ │
│ │ Permissions:                                            │ │
│ │ • Manage posts                                          │ │
│ │ • Read insights                                         │ │
│ │                                                         │ │
│ │ Connected: 15 days ago                                  │ │
│ │                                                         │ │
│ │ [Disconnect] [Refresh Token]                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ TikTok                                                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ✗ Not Connected                                         │ │
│ │                                                         │ │
│ │ Connect your TikTok account to publish video content    │ │
│ │                                                         │ │
│ │ [Connect TikTok Account]                                │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Disconnect Confirmation:**
```
┌───────────────────────────────────────┐
│ Disconnect Instagram?       [✕ Close] │
├───────────────────────────────────────┤
│                                       │
│ ⚠️ Warning                            │
│                                       │
│ Disconnecting @yourbrand will:        │
│ • Stop publishing to Instagram        │
│ • Stop collecting metrics             │
│ • Affect 3 active campaigns           │
│                                       │
│ You can reconnect anytime.            │
│                                       │
│ [Cancel] [Disconnect]                 │
└───────────────────────────────────────┘
```

---

### 8.3 Ad Accounts Tab ⭐ NEW
**Route:** `/settings/ad-accounts`
**Purpose:** Manage Meta ad accounts for boosting posts

```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                                    │
├─────────────────────────────────────────────────────────────┤
│ Profile | Connected Accounts | [Ad Accounts] | Notifications│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Meta Ad Accounts                                            │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ My Business Ad Account                                  │ │
│ │ Account ID: act_123456789                               │ │
│ │                                                         │ │
│ │ Status: ACTIVE ● | Currency: USD                       │ │
│ │ Balance: $500.00                                        │ │
│ │ Spend Cap: $1,000/month                                 │ │
│ │ Amount Spent (This Month): $245.80                      │ │
│ │                                                         │ │
│ │ Connected: 2 days ago                                   │ │
│ │ Last sync: 5 minutes ago                                │ │
│ │                                                         │ │
│ │ Active Boosts: 2                                        │ │
│ │ Total Spent (All Time): $1,245.80                       │ │
│ │                                                         │ │
│ │ [View Boosts] [Sync Balance] [Disconnect]              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [+ Connect Another Ad Account]                              │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ ℹ️ About Ad Accounts                                        │
│                                                             │
│ To boost posts, you need a Meta Ad Account with an active  │
│ payment method. Your credit card will be charged directly   │
│ by Meta for ad spend - CoClub does not process or handle   │
│ payments for advertising.                                   │
│                                                             │
│ [Learn More About Boosting] [Setup Guide]                  │
└─────────────────────────────────────────────────────────────┘
```

**Connect Ad Account Flow:**
```
1. Click "+ Connect Another Ad Account"
2. OAuth redirect to Meta
3. User selects ad account from their Meta Business Manager
4. CoClub fetches account details via API
5. Account appears in list
```

---

## 9. Notifications & Alerts

### 9.1 Notifications Center
**Route:** Dropdown from header bell icon
**Purpose:** View all app notifications

**Dropdown Panel:**
```
┌─────────────────────────────────────────────────────────────┐
│ Notifications                           [Mark All as Read] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 🚀 2 posts recommended for boosting                         │
│ Campaign: Spring Collection                                 │
│ 2 hours ago                                                 │
│ [View Recommendations]                                      │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ ✓ Campaign completed successfully                           │
│ Campaign: Spring Collection                                 │
│ 3 hours ago                                                 │
│ [View Report]                                               │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ 📊 Your post is performing exceptionally well!              │
│ Post #2 exceeded expected saves by 180%                     │
│ 1 day ago                                                   │
│ [View Post Analytics]                                       │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ ⚠️ Instagram token expiring soon                            │
│ Please reconnect your account by May 15                     │
│ 2 days ago                                                  │
│ [Reconnect Now]                                             │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ ✓ Boost campaign started                                    │
│ Post: "How to choose stocking shade"                        │
│ 3 days ago                                                  │
│ [View Performance]                                          │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ [View All Notifications]                                    │
└─────────────────────────────────────────────────────────────┘
```

**Notification Types:**
- Campaign completed
- Post published
- Boost recommendations ready
- Performance milestones (e.g., 1000 impressions)
- Token expiring
- Boost started/paused/completed
- Budget warnings (ad spend approaching limit)

---

### 9.2 Notification Preferences
**Route:** `/settings/notifications`
**Purpose:** Control notification delivery

```
┌─────────────────────────────────────────────────────────────┐
│ Notification Preferences                          [Save] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Email Notifications                                         │
│ Send to: user@example.com                                   │
│                                                             │
│ [✓] Campaign completed                                      │
│ [✓] Post published successfully                             │
│ [✓] AI boost recommendations available                      │
│ [✓] Performance milestones reached                          │
│ [ ] Weekly performance summary                              │
│ [✓] Token expiration warnings                               │
│ [ ] Daily digest                                            │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ In-App Notifications                                        │
│ [✓] All notifications                                       │
│ [✓] Show badge count                                        │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Push Notifications (Mobile App)                             │
│ [✓] Campaign updates                                        │
│ [✓] Performance alerts                                      │
│ [ ] Daily digest                                            │
│ [✓] Boost recommendations                                   │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ [Save Preferences]                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Media Library

### 10.1 Media Library Screen (Optional Enhancement)
**Route:** `/media`
**Purpose:** Centralized asset management

```
┌─────────────────────────────────────────────────────────────┐
│ Media Library                               [+ Upload Media] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [🔍 Search] [All Types ▼] [All Brands ▼] [Grid ⚏] [List ☰]│
│                                                             │
│ ┌───────┬───────┬───────┬───────┬───────┬───────┐          │
│ │ [IMG] │ [IMG] │ [IMG] │ [PDF] │ [VID] │ [IMG] │          │
│ │       │       │       │       │       │       │          │
│ │ Logo  │ Prod  │ Brand │ Guide │ Demo  │ Hero  │          │
│ │ 580KB │ 1.2MB │ 800KB │ 2.4MB │ 5.8MB │ 1.5MB │          │
│ │       │       │       │       │       │       │          │
│ │ [✓]   │ [✓]   │       │       │       │       │          │
│ └───────┴───────┴───────┴───────┴───────┴───────┘          │
│                                                             │
│ Selected: 2 items                                           │
│ [Download] [Delete] [Add to Campaign]                       │
│                                                             │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                                             │
│ Storage Used: 45.2 MB / 5 GB                                │
│ Total Files: 127                                            │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Upload images, videos, PDFs
- Tag by brand/product
- Search and filter
- Bulk operations
- Storage quota management

---

## MVP Phase Prioritization

### Phase 1: Core Functionality (Launch)
**Goal:** Users can create campaigns and publish content

1. ✅ Landing Page
2. ✅ Sign Up/Sign In
3. ✅ Onboarding Wizard
4. ✅ Dashboard
5. ✅ Brand Create/Edit
6. ✅ Product Create/Edit
7. ✅ Campaign Brief (Step 1)
8. ✅ Campaign Scoping (Step 2)
9. ✅ Content Review/Edit
10. ✅ Publishing Confirmation
11. ✅ Connected Accounts Settings

**Priority:** Must have for MVP launch

---

### Phase 2: Analytics & Boost (Post-Launch)
**Goal:** Users see performance and can boost top posts

12. ⭐ Campaign Dashboard (Post-Publish)
13. ⭐ Post Detail Analytics
14. ⭐ Campaign Report View
15. ⭐ Boost Configuration Modal
16. ⭐ Active Boosts Dashboard
17. ⭐ Boost Performance Detail
18. ⭐ Ad Accounts Settings Tab
19. ⭐ Notifications Center

**Priority:** High - enables monetization through boost feature

---

### Phase 3: Enhancement (Future)
**Goal:** Advanced analytics and insights

20. Analytics Dashboard
21. Content Performance Insights
22. Media Library
23. Notification Preferences
24. Advanced targeting options
25. A/B testing features

**Priority:** Medium - nice to have, improves UX

---

## Design System Guide

### Key UI Components Needed

**1. Cards**
- Campaign card (list view)
- Post card (with metrics)
- Metric card (stat display)
- Brand card
- Product card
- Notification card
- Boost recommendation card ⭐

**2. Forms**
- Multi-step wizard (campaign creation)
- Single-page forms (brand, product)
- File upload zones (drag & drop)
- Structured brief form ⭐

**3. Modals**
- Confirmation dialogs
- Boost configuration ⭐
- Publishing progress
- Edit content
- Warning/error messages

**4. Tables/Lists**
- Campaign list
- Post list
- Boost list ⭐
- Media library grid

**5. Charts & Graphs**
- Line charts (performance over time)
- Bar charts (campaign comparison)
- Pie charts (demographics)
- Multi-line graphs (boost metrics) ⭐

**6. Status Indicators**
- Badges (Draft, Active, Completed)
- Progress bars (generation, publishing)
- Loading spinners
- Status dots (●) with colors

**7. Special Components**
- AI recommendation banners ⭐
- Metric cards with trend indicators (↑ ↓)
- Chat interface (campaign scoping)
- Performance tier badges (⭐⭐⭐)
- Boost confidence indicators ⭐

---

### Color System

**Status Colors:**
- **Success/Excellent:** Green (#10B981)
- **Good/Active:** Blue (#3B82F6)
- **Warning/Pending:** Yellow (#F59E0B)
- **Error/Poor:** Red (#EF4444)
- **Neutral/Draft:** Gray (#6B7280)

**Feature Colors:**
- **AI Features:** Purple gradient (#8B5CF6 → #EC4899) ⭐
- **Boost:** Orange/Gold (#F97316) ⭐
- **Primary CTA:** Brand color (your choice)

**Performance Tiers:**
- Excellent: 3 gold stars ⭐⭐⭐
- Good: 2 blue stars ⭐⭐
- Average: 1 star ⭐
- Poor: No stars

---

### Typography Scale

**Headers:**
- H1: 2.5rem (40px) - Page titles
- H2: 2rem (32px) - Section headers
- H3: 1.5rem (24px) - Card titles
- H4: 1.25rem (20px) - Subsections

**Body:**
- Large: 1.125rem (18px) - Important text
- Regular: 1rem (16px) - Default
- Small: 0.875rem (14px) - Captions
- Tiny: 0.75rem (12px) - Labels

---

### Spacing System
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px

---

### Icon Library Needed
- Social platform icons (Instagram, Facebook, TikTok)
- Action icons (Edit, Delete, View, Download)
- Status icons (✓ ✗ ⏳ 🟢 🔴)
- Feature icons (🤖 💡 🚀 📊 ⭐)
- Navigation icons (Dashboard, Settings, Analytics)

---

### Empty States

**No Campaigns Yet:**
```
┌───────────────────────────────────┐
│                                   │
│         📊                        │
│                                   │
│   No campaigns created yet        │
│                                   │
│   Create your first campaign to   │
│   start publishing AI-powered     │
│   content to social media         │
│                                   │
│   [+ Create Campaign]             │
│                                   │
└───────────────────────────────────┘
```

**No Connected Accounts:**
```
┌───────────────────────────────────┐
│                                   │
│         🔗                        │
│                                   │
│   No accounts connected           │
│                                   │
│   Connect Instagram, Facebook, or │
│   TikTok to start publishing      │
│                                   │
│   [Connect Accounts]              │
│                                   │
└───────────────────────────────────┘
```

**No Boost Recommendations:**
```
┌───────────────────────────────────┐
│                                   │
│         💡                        │
│                                   │
│   No boost recommendations yet    │
│                                   │
│   AI will recommend posts to boost│
│   after campaigns complete (72hrs)│
│                                   │
│   [View Active Campaigns]         │
│                                   │
└───────────────────────────────────┘
```

---

### Loading States

**Content Generation:**
```
🤖 AI is creating your content...
[====================] 100%
✓ Generated 9 variants
⏳ Estimated time: ~2 minutes
```

**Publishing:**
```
⏳ Publishing posts...
✓ Instagram Post 1/3 - Published
⏳ Instagram Post 2/3 - Publishing...
```

**Data Sync:**
```
🔄 Syncing metrics from Meta...
⏳ This may take a few seconds
```

---

### Responsive Breakpoints

- **Mobile:** < 640px (sm)
- **Tablet:** 640px - 1024px (md, lg)
- **Desktop:** > 1024px (xl, 2xl)

**Mobile Considerations:**
- Hamburger menu navigation
- Bottom tab bar
- Stacked stat cards
- Simplified charts
- Full-width modals
- Swipeable galleries

---

## Summary

**Total Screens: 29**

| Category | Screens | Priority |
|---|---|---|
| Authentication | 4 | Phase 1 |
| Dashboard | 1 | Phase 1 |
| Brand Management | 3 | Phase 1 |
| Product Management | 2 | Phase 1 |
| Campaign Management | 7 | Phase 1 |
| Boost Features | 3 | Phase 2 ⭐ |
| Analytics | 3 | Phase 2-3 |
| Settings | 3 | Phase 1-2 |
| Notifications | 2 | Phase 2 |
| Media Library | 1 | Phase 3 |

**Key Features:**
- ✅ AI-powered content generation
- ✅ Multi-platform publishing
- ✅ Campaign performance tracking
- ⭐ AI boost recommendations (NEW)
- ⭐ Meta Ads integration (NEW)
- ✅ Real-time metrics polling
- ✅ Performance insights

---

**You're ready to wireframe! 🎨**

This document provides complete specifications for all screens with:
- Visual layouts
- Component details
- User flows
- Data requirements
- API integration points
- Design system guidelines

Use this as your single source of truth for creating wireframes in Figma, Sketch, or your preferred design tool.
