# CoClub SME Platform - System Architecture

**Version:** 1.0
**Last Updated:** September 2026
**Status:** Production

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Breakdown](#component-breakdown)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [External Integrations](#external-integrations)
7. [Background Job System](#background-job-system)
8. [Security & Authentication](#security--authentication)
9. [Deployment Architecture](#deployment-architecture)
10. [Key Design Decisions](#key-design-decisions)

---

## System Overview

### Purpose
CoClub SME is an AI-powered social media campaign management platform that helps small and medium enterprises (SMEs) create, manage, and analyze multi-platform social media campaigns.

### Core Capabilities
- **AI-Powered Content Creation**: Generate campaign variants with message angles, images, videos, and captions
- **Multi-Platform Publishing**: Post to Instagram, Facebook, and TikTok
- **Campaign Scoping**: Conversational AI agent that plans campaign structure before generation
- **Performance Analytics**: Automated metrics tracking with AI-generated insights
- **Content Analysis**: AI-powered recommendations based on historical performance

### Technology Stack
- **Frontend**: Next.js 14 (React, TypeScript)
- **Backend API**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (via Supabase)
- **Storage**: Supabase Storage (S3-compatible)
- **Authentication**: Supabase Auth (JWT-based)
- **Background Jobs**: APScheduler with PostgreSQL jobstore
- **Containerization**: Docker + Docker Compose

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                      (Next.js Frontend)                              │
│                     http://localhost:3000                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ HTTP/REST API
                             │ JWT Authentication
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       API LAYER                                      │
│                    (FastAPI - sme-api)                               │
│                   http://localhost:8000                              │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Routers: campaigns, brands, products, social, assets        │   │
│  │  Services: llm, image_gen, social, scheduler, content_analysis│  │
│  │  Pipeline: intake → variants → copywriting → post → feedback │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────┬──────────────────────────────┬────────────────────┘
                 │                              │
                 │                              │ Job Scheduling
                 │                              │
                 │                   ┌──────────▼──────────┐
                 │                   │  BACKGROUND WORKER   │
                 │                   │   (sme-worker)       │
                 │                   │                      │
                 │                   │ • Media Generation   │
                 │                   │ • Metrics Polling    │
                 │                   │ • Video Processing   │
                 │                   │ • Report Generation  │
                 │                   └──────────────────────┘
                 │
                 │
┌────────────────▼────────────────────────────────────────────────────┐
│                     DATA LAYER                                       │
│                  (Supabase / PostgreSQL)                             │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │   Database       │  │   Storage        │  │   Auth          │  │
│  │   (PostgreSQL)   │  │   (S3-like)      │  │   (JWT)         │  │
│  │                  │  │                  │  │                 │  │
│  │ • campaigns      │  │ • brand-assets   │  │ • User tokens   │  │
│  │ • variants       │  │ • products       │  │ • Sessions      │  │
│  │ • posts          │  │ • campaign-      │  │ • RLS policies  │  │
│  │ • post_metrics   │  │   variants       │  │                 │  │
│  │ • captions       │  │ • moodboards     │  │                 │  │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                    EXTERNAL SERVICES                                 │
│                                                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐ ┌─────────────────┐ │
│  │ Anthropic   │ │  OpenAI     │ │  Luma    │ │  ElevenLabs     │ │
│  │ (Claude)    │ │  (DALL-E 2) │ │  (Video) │ │  (Audio/Music)  │ │
│  └─────────────┘ └─────────────┘ └──────────┘ └─────────────────┘ │
│                                                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────┐                      │
│  │  Instagram  │ │  Facebook   │ │  TikTok  │                      │
│  │  Graph API  │ │  Graph API  │ │  API     │                      │
│  └─────────────┘ └─────────────┘ └──────────┘                      │
└───────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Frontend (sme-web)

**Technology**: Next.js 14 with App Router, React, TypeScript, Tailwind CSS

**Key Features**:
- Server-side rendering (SSR) for initial page load
- Client-side navigation for SPA experience
- Real-time campaign status polling
- File upload with drag-and-drop
- Responsive design for mobile/desktop

**Directory Structure**:
```
apps/sme/sme-web/
├── app/                    # Next.js App Router pages
│   ├── intake/            # Campaign creation wizard
│   ├── campaign/          # Campaign detail views
│   ├── settings/          # User settings (social accounts)
│   └── layout.tsx         # Root layout with auth
├── lib/
│   ├── api.ts             # API client with auth headers
│   └── supabaseClient.ts  # Supabase client config
└── components/            # Reusable UI components
```

**State Management**: React hooks + local state (no Redux/Zustand needed)

**API Communication**:
- RESTful HTTP calls via `fetch`
- JWT tokens from Supabase Auth in `Authorization` header
- Polling for campaign status updates (every 5 seconds)

---

### 2. Backend API (sme-api)

**Technology**: FastAPI, Python 3.12, Pydantic for validation

**Architecture Pattern**: Layered architecture with clear separation

```
app/
├── routers/           # API endpoints (HTTP layer)
│   ├── campaigns.py   # Campaign CRUD + workflow endpoints
│   ├── brands.py      # Brand management
│   ├── products.py    # Product catalog
│   ├── social.py      # Social account OAuth + posting
│   ├── assets.py      # File upload endpoints
│   ├── tracking.py    # UTM links, follower tracking
│   └── reports.py     # Analytics and insights
├── services/          # Business logic (service layer)
│   ├── llm.py         # AI prompt engineering (Claude)
│   ├── image_gen.py   # Image generation (OpenAI)
│   ├── luma.py        # Video generation
│   ├── social.py      # Platform API integrations
│   ├── scheduler.py   # Background job scheduling
│   ├── content_analysis.py  # Performance analysis
│   └── scoring.py     # Engagement score calculation
├── pipeline/          # Campaign workflow pipeline
│   ├── step1_intake.py       # Brand/product extraction
│   ├── step2_variants.py     # Variant generation
│   ├── step3_copywriting.py  # Caption generation
│   ├── step4_approve_post.py # Publishing to platforms
│   └── step5_feedback.py     # Metrics + reports
├── models/
│   └── schemas.py     # Pydantic models for validation
├── db.py              # Supabase client factory
├── config.py          # Environment config
└── main.py            # FastAPI app + CORS setup
```

**Key Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/brands` | POST | Create brand with guideline extraction |
| `/v1/products` | POST | Add product with asset analysis |
| `/v1/campaigns` | POST | Create campaign (starts pipeline) |
| `/v1/campaigns/{id}/scope/messages` | POST | Conversational scoping agent |
| `/v1/campaigns/{id}/scope/confirm` | POST | Confirm scope, trigger variant generation |
| `/v1/campaigns/{id}/generate-media` | POST | Generate images/videos for variants |
| `/v1/campaigns/{id}/generate-copy` | POST | Generate captions |
| `/v1/campaigns/{id}/approve` | POST | Mark variants for posting |
| `/v1/campaigns/{id}/post` | POST | Publish to social platforms |
| `/v1/campaigns/{id}/metrics/refresh` | POST | Manual metrics refresh |
| `/v1/campaigns/{id}/report` | GET | Get AI-generated performance report |
| `/social/connect/{platform}` | POST | OAuth flow for Instagram/Facebook/TikTok |

---

### 3. Background Worker (sme-worker)

**Technology**: Same Python codebase as API, runs `python -m app.worker`

**Purpose**: Execute long-running tasks asynchronously to avoid HTTP timeouts

**Job Types**:

1. **Media Generation** (`schedule_variant_media_generation`)
   - Triggered: When user confirms campaign scope
   - Duration: 5-30 minutes (multiple AI API calls)
   - Process:
     - Download brand/product reference images
     - For each variant:
       - Generate image (OpenAI `gpt-image-2`)
       - Quality check (Claude vision)
       - Retry up to 2 times if quality insufficient
       - Upload to Supabase Storage
     - For videos: Call Luma API, poll for completion

2. **Metrics Polling** (`schedule_metrics_polling`)
   - Triggered: After campaign posts published
   - Frequency: Every 1 hour
   - Duration: 72 hours (3 days)
   - Process:
     - Fetch metrics from Instagram/Facebook/TikTok APIs
     - Insert new `post_metrics` row (time-series data)
     - Calculate engagement score

3. **Video Generation Polling** (`schedule_video_generation_poll`)
   - Triggered: When Luma video generation starts
   - Frequency: Every 15 seconds
   - Max duration: 30 minutes
   - Process: Poll Luma API until video is ready

4. **Feedback Report** (`schedule_feedback_job`)
   - Triggered: 24 hours after campaign posts
   - One-time job
   - Process:
     - Refresh metrics one final time
     - Calculate performance tiers
     - Generate AI narrative report
     - Mark campaign as "completed"

**Scheduling Technology**: APScheduler with PostgreSQL jobstore
- Jobs survive process restarts
- No duplicate execution across multiple workers
- Configurable misfire grace time

---

### 4. Database (PostgreSQL via Supabase)

**Schema Version**: See `supabase/migrations/`

**Core Tables**:

#### `campaigns`
Main campaign entity
```sql
- id (uuid, PK)
- user_id (uuid, FK → auth.users)
- brand_id (uuid, FK → brands)
- product_id (uuid, FK → products, nullable)
- campaign_type (enum: product_launch, branding, promotional)
- status (enum: scoping, generating_variants, ready_for_copy, ...)
- brief (text) - Simple brief (backward compat)
- structured_brief (jsonb) - Structured 9-field brief
- content_plan (jsonb) - Scoped campaign structure
- created_at, updated_at
```

#### `variants`
Individual creative variations
```sql
- id (uuid, PK)
- campaign_id (uuid, FK)
- message_angle (text) - Core creative concept
- image_prompt (text) - Prompt sent to image gen
- image_url (text) - Generated image
- media_type (enum: image, video)
- video_url (text, nullable)
- voiceover_script (text, nullable)
- music_prompt (text, nullable)
- status (enum: pending, approved, rejected)
- target_platforms (text[]) - For scoped campaigns
```

#### `captions`
Platform-specific copy
```sql
- id (uuid, PK)
- variant_id (uuid, FK)
- platform (enum: instagram, facebook, tiktok)
- caption_text (text)
- hashtags (text[])
- UNIQUE(variant_id, platform) - One caption per platform per variant
```

#### `posts`
Published content tracking
```sql
- id (uuid, PK)
- variant_id (uuid, FK)
- platform (enum)
- external_post_id (text) - Platform's post ID
- status (enum: pending, posted, failed)
- posted_at (timestamptz)
- error_message (text, nullable)
```

#### `post_metrics`
**Time-series metrics data** (new row per poll)
```sql
- id (uuid, PK)
- post_id (uuid, FK)
- likes, comments, shares, views (integer)
- reach, saves, profile_visits, reposts (integer)
- impressions, post_clicks (integer)
- avg_watch_time_seconds, total_watch_time_seconds (video)
- link_clicks, add_to_cart_count, conversion_count (UTM tracking)
- conversion_value (decimal)
- fetched_at (timestamptz) - When this snapshot was taken
```

**Key Design**: Each metrics poll creates a **new row** - enables time-series analysis

#### `campaign_reports`
AI-generated performance summaries
```sql
- id (uuid, PK)
- campaign_id (uuid, FK)
- summary_text (text) - AI narrative
- top_variant_id (uuid, FK → variants)
- verdicts (jsonb) - Detailed performance breakdown
- follower_growth (jsonb) - Follower changes during campaign
- created_at (timestamptz)
```

#### `social_accounts`
Connected social media accounts
```sql
- id (uuid, PK)
- user_id (uuid, FK)
- platform (enum)
- platform_user_id (text)
- username (text)
- encrypted_token (text) - Fernet-encrypted access token
- token_expires_at (timestamptz, nullable)
- created_at, updated_at
```

**Security**: Row-Level Security (RLS) policies ensure users only access their own data

---

## Data Flow

### Campaign Creation Flow

```
1. USER: Create campaign via /intake page
   ↓
2. FRONTEND: POST /v1/campaigns
   Body: { brand_id, product_id, campaign_type, structured_brief }
   ↓
3. API: Insert campaigns table, status = "scoping"
   Return campaign_id
   ↓
4. FRONTEND: Navigate to /campaign/{id}
   Start conversational scoping
   ↓
5. USER: Chat with scoping agent
   "I need 9 Instagram posts for a product launch"
   ↓
6. FRONTEND: POST /v1/campaigns/{id}/scope/messages
   Body: { text: "...", image_urls: [...] }
   ↓
7. API: llm.continue_campaign_scoping()
   - Claude analyzes request + brand/product context
   - Returns: { kind: "question", text: "..." }
     OR { kind: "plan", items: [...], summary: "..." }
   ↓
8. FRONTEND: Display question OR show plan for approval
   ↓
9. USER: Approve plan
   ↓
10. FRONTEND: POST /v1/campaigns/{id}/scope/confirm
    Body: { plan_item_references: [...] }
    ↓
11. API:
    - Update campaigns.content_plan
    - Insert variant rows (status = "pending")
    - Update campaigns.status = "generating_variants"
    - Call schedule_variant_media_generation()
    ↓
12. WORKER: run_variant_media_generation_job()
    - Download brand guidelines + product assets
    - For each variant:
      - Generate image (OpenAI)
      - Quality check (Claude vision)
      - Retry if needed
      - Upload to storage
      - Update variants.image_url
    - Update campaigns.status = "ready_for_copy"
    ↓
13. FRONTEND: Polling detects status change
    Display "Generate Copy" button
    ↓
14. USER: Click "Generate Copy"
    ↓
15. FRONTEND: POST /v1/campaigns/{id}/generate-copy
    ↓
16. API: pipeline.step3_copywriting.run_copywriting()
    - For each variant:
      - llm.write_captions() - one per platform
      - Insert into captions table
    - Update campaigns.status = "ready_for_review"
    ↓
17. FRONTEND: Display all variants with images + captions
    User selects which to approve
    ↓
18. USER: Approve variants
    ↓
19. FRONTEND: POST /v1/campaigns/{id}/approve
    Body: { approved_variant_ids: [...] }
    ↓
20. API: Update variants.status = "approved"
    Update campaigns.status = "ready_to_post"
    ↓
21. USER: Click "Post Now"
    ↓
22. FRONTEND: POST /v1/campaigns/{id}/post
    ↓
23. API: pipeline.step4_approve_post.post_campaign()
    - For each approved variant:
      - For each platform:
        - Call social.post_to_platform()
        - Insert posts table with external_post_id
    - Update campaigns.status = "posted"
    - Call schedule_metrics_polling() (hourly for 72h)
    - Call schedule_feedback_job() (runs in 24h)
    ↓
24. WORKER: Metrics polling starts (every 1 hour)
    - Fetch likes, comments, shares, reach, etc.
    - Insert post_metrics row
    ↓
25. WORKER: 24 hours later, run_feedback_job()
    - Refresh metrics one final time
    - Calculate engagement scores
    - llm.narrate_report() - AI analysis
    - Insert campaign_reports
    - Update campaigns.status = "completed"
```

### Metrics Polling Flow

```
POST published at 10:00 AM
    ↓
schedule_metrics_polling() creates APScheduler job
    - Interval: 1 hour
    - Duration: 72 hours
    - First run: 11:00 AM (+ random jitter ±15min)
    ↓
Every hour for 3 days:
    WORKER: run_scheduled_metrics_refresh()
    ↓
    For each posted post:
        - social.fetch_metrics(platform, external_post_id)
        - Call Instagram/Facebook Graph API
        - Get: likes, comments, shares, reach, saves, etc.
        - INSERT INTO post_metrics (new row, don't overwrite)
    ↓
    Return fetched data
    ↓
FRONTEND: User can view metrics graph
    - GET /v1/campaigns/{id}/metrics/history
    - Returns all post_metrics rows (time-series)
    - Chart shows growth over time
```

---

## External Integrations

### 1. Anthropic Claude (AI)

**Purpose**:
- Content generation (message angles, captions)
- Quality checks (image generation validation)
- Performance analysis (report narration)
- Campaign scoping (conversational agent)

**API Calls**:
- `llm.continue_campaign_scoping()` - Scoping conversation
- `llm.ideate_message_angles()` - Generate creative concepts
- `llm.write_captions()` - Platform-specific copy
- `llm.narrate_report()` - Performance insights
- `llm.analyze_content_performance()` - AI recommendations

**Model**: `claude-sonnet-4.5` (configurable via `ANTHROPIC_MODEL`)

**Token Tracking**: All usage logged to `usage_events` table

---

### 2. OpenAI DALL-E 2 (Image Generation)

**Purpose**: Generate campaign images from prompts

**Endpoint**: `POST https://api.openai.com/v1/images/edits`

**Flow**:
1. `image_gen.generate_and_check()` sends prompt + reference images
2. OpenAI returns image URL
3. `llm.quality_check_image()` validates with Claude vision
4. Retry up to `MAX_QUALITY_RETRIES` (2) if insufficient quality
5. Download image, upload to Supabase Storage

**Model**: `gpt-image-2` (configurable via `OPENAI_IMAGE_MODEL`)

---

### 3. Luma (Video Generation)

**Purpose**: Image-to-video generation for video campaigns

**API**: Luma Agents API (`platform.lumalabs.ai`)

**Flow**:
1. `luma.create_generation()` - Submit image + motion prompt
2. Returns `generation_id`
3. `schedule_video_generation_poll()` - Poll every 15s
4. `luma.check_status()` until status = "completed"
5. Download video from `generation.video.url`
6. If voiceover/music requested: Mix audio with `audio_mix.mix_and_mux()`

**Max Poll Time**: 30 minutes before marking as failed

---

### 4. ElevenLabs (Audio)

**Purpose**: Voiceover + background music for videos

**Services Used**:
- **Text-to-Speech**: `elevenlabs_tts.generate_voiceover()`
  - Model: `eleven_v3` (for expressiveness)
- **Music Generation**: `elevenlabs_music.generate_music()`
  - Length: Matches video duration

**Audio Mixing**: `audio_mix.mix_and_mux()`
- Uses `ffmpeg` binary (system dependency)
- Combines: Video + Voiceover + Music
- Returns: Final muxed MP4

---

### 5. Social Platform APIs

#### Instagram Graph API

**OAuth Scope**: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`

**Endpoints Used**:
- `POST /{ig-user-id}/media` - Create media container
- `POST /{ig-user-id}/media_publish` - Publish post
- `GET /{media-id}/insights` - Fetch metrics (reach, saves, etc.)

#### Facebook Graph API

**OAuth Scope**: `pages_manage_posts`, `pages_read_engagement`, `pages_show_list`

**Endpoints Used**:
- `POST /{page-id}/photos` - Post image
- `POST /{page-id}/videos` - Post video
- `GET /{post-id}?fields=shares,likes.summary(true),comments.summary(true)` - Metrics

#### TikTok Content Posting API

**OAuth Scope**: `video.publish`, `video.list`

**Endpoints Used**:
- `POST /share/video/upload/` - Upload video
- Note: TikTok doesn't expose post-level insights, metrics return zeros

**Token Encryption**: All access tokens encrypted with Fernet (symmetric encryption)
- Key: `SOCIAL_TOKEN_ENCRYPTION_KEY` environment variable
- Stored in `social_accounts.encrypted_token`

---

## Background Job System

### APScheduler Architecture

**Jobstore**: PostgreSQL (via `DATABASE_URL`)
- Jobs persist across restarts
- Multiple workers safe (only one executes each job)
- Heartbeat mechanism for job discovery

**Executor**: ThreadPoolExecutor
- `MAX_CONCURRENT_JOBS = 5` (prevents thundering herd)
- Parallel execution for independent jobs

**Scheduler States**:
- **API Process** (`sme-api`): Scheduler runs in "paused" mode
  - Only adds jobs to store
  - Never executes (prevents duplicate execution)
- **Worker Process** (`sme-worker`): Scheduler runs actively
  - Polls jobstore every 3 seconds (heartbeat)
  - Executes due jobs

### Job Configuration

**Misfire Grace Time**: `None` (infinite)
- Reason: Default 1-second grace causes jobs to silently drop if noticed late
- With `None`: Job runs whenever noticed, even if delayed

**Jitter**: Random offset to prevent simultaneous execution
- Example: Metrics polling has ±15 minute jitter
- Spreads load across time window

### Job Lifecycle

```
API: add_job() → PostgreSQL jobstore
    ↓
Worker heartbeat (every 3s)
    ↓
Worker: Check jobstore for due jobs
    ↓
If job due: Execute in thread pool
    ↓
Job completes: Update or remove from jobstore
```

---

## Security & Authentication

### Authentication Flow

1. **User Registration/Login**: Handled by Supabase Auth
   - Email/password or OAuth (Google, etc.)
   - Returns JWT access token

2. **Frontend**: Stores token in `supabaseClient`
   - Automatically refreshed when expired

3. **API Requests**: Token sent in `Authorization: Bearer <token>` header

4. **API Validation**: `app/routers/campaigns.py` (example)
   ```python
   async def get_user_id(token: str = Depends(get_bearer_token)) -> str:
       # Verify JWT with Supabase Auth
       user = supabase.auth.get_user(token)
       return user.id
   ```

### Row-Level Security (RLS)

**Database-level access control** - users can only see their own data

Example policy:
```sql
CREATE POLICY "campaigns_owner_all" ON campaigns
  FOR ALL USING (auth.uid() = user_id);
```

All tables with `user_id` have similar policies.

### Service Role Access

**sme-api and sme-worker** use `SUPABASE_SERVICE_ROLE_KEY`
- Bypasses RLS for background jobs
- Required for operations without user context (e.g., scheduled metrics polling)

### Token Encryption

Social platform tokens encrypted at rest:
- Algorithm: Fernet (symmetric encryption)
- Key: `SOCIAL_TOKEN_ENCRYPTION_KEY` (32-byte base64)
- Stored: `social_accounts.encrypted_token`
- Decrypted: Only when needed for API calls

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
services:
  sme-api:
    - Port: 8000
    - Env: .env
    - Purpose: HTTP API server

  sme-worker:
    - No ports (internal only)
    - Same image as sme-api
    - Command: python -m app.worker
    - Purpose: Background job execution

  sme-web:
    - Port: 3000
    - Env: .env.local
    - Build args: NEXT_PUBLIC_API_URL, etc.
    - Purpose: Next.js frontend
```

### Production Considerations

**API Scaling**:
- Run multiple `sme-api` replicas behind load balancer
- All replicas share same PostgreSQL jobstore
- Scheduler remains paused in all replicas

**Worker Scaling**:
- Run **exactly one** `sme-worker` instance
- Reason: APScheduler with PostgreSQL jobstore ensures single execution
- Scaling workers horizontally currently unsupported

**Database**:
- Use managed PostgreSQL (Supabase hosted)
- Connection pooling via Supabase
- Regular backups (Supabase Point-in-Time Recovery)

**Storage**:
- Supabase Storage (S3-compatible)
- CDN for asset delivery
- Automatic CORS configuration

**Environment Variables**:
- Use secret management (AWS Secrets Manager, Vault, etc.)
- Never commit `.env` files
- Rotate API keys regularly

---

## Key Design Decisions

### 1. Why Separate Worker Process?

**Problem**: Image/video generation takes 5-30 minutes, causing HTTP timeouts

**Solution**:
- API schedules jobs, returns immediately
- Worker executes jobs asynchronously
- Frontend polls for status updates

**Alternative Considered**: Celery + Redis
- **Rejected**: APScheduler + PostgreSQL simpler, fewer dependencies

---

### 2. Why Time-Series Metrics (New Row Per Poll)?

**Problem**: Need to track engagement growth over time

**Solution**: Each poll creates new `post_metrics` row with `fetched_at` timestamp

**Benefits**:
- Historical trend analysis
- Engagement velocity calculation
- No data loss (vs. overwriting)

**Alternative Considered**: Single row, update on each poll
- **Rejected**: Loses historical data, can't build growth charts

---

### 3. Why Structured Brief + Simple Brief?

**Problem**: Detailed briefs improve AI quality, but some users want quick campaigns

**Solution**: Support both modes
- **Structured Brief**: 9 fields (objective, target_audience, USP, etc.)
- **Simple Brief**: Free-text "Surprise Me" mode

**Implementation**:
- Store both in database (`brief` text + `structured_brief` jsonb)
- Auto-sync structured → simple for backward compatibility

---

### 4. Why Campaign Scoping Agent?

**Problem**: Fixed campaign sizes don't fit all use cases

**Solution**: Conversational AI that asks questions and builds custom plan
- "How many posts?" → "9 Instagram posts"
- "Voiceover for videos?" → "Yes/No"
- Plan confirmed before generation starts

**Benefits**:
- Flexible campaign structures
- Better user experience (guided workflow)
- Reduces wasted generation (user confirms before spending credits)

---

### 5. Why Platform-Specific Caption Structures?

**Problem**: One-size-fits-all captions underperform on each platform

**Solution**: Different prompt templates per platform
- **Instagram**: Hook → Benefit → CTA
- **Facebook**: Problem → Solution → Benefit → Promotion → CTA
- **TikTok**: Short, video-supporting caption

**Data Source**: User's historical performance data validated these structures

---

### 6. Why Visual Variety Enforcement?

**Problem**: AI was generating identical-looking images despite different message angles

**Solution**: Enhanced image prompts with explicit diversity requirements
- Vary: Composition, color treatment, mood, background, mascot pose
- Treat brand guidelines as "toolkit to mix and match" not "rigid template"

**Result**: 9 variants now look visually distinct while staying on-brand

---

## Appendix: Environment Variables

### Required
- `ANTHROPIC_API_KEY` - Claude API access
- `OPENAI_API_KEY` - Image generation
- `SUPABASE_URL` - Database/storage
- `SUPABASE_SERVICE_ROLE_KEY` - Backend access
- `SOCIAL_TOKEN_ENCRYPTION_KEY` - Encrypt social tokens

### Optional (Features Degrade Gracefully)
- `LUMA_API_KEY` - Video generation (fails cleanly without)
- `ELEVENLABS_API_KEY` - Audio (silent videos without)
- `META_APP_ID`, `META_APP_SECRET` - Facebook/Instagram posting
- `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` - TikTok posting
- `DATABASE_URL` - Persistent job scheduling (in-memory fallback)

### Development
- `CORS_ALLOW_ORIGINS` - Frontend URL (default: http://localhost:3000)
- `NEXT_PUBLIC_API_URL` - API URL for browser (default: http://localhost:8000)

---

## Appendix: Database Migrations

**Location**: `supabase/migrations/`

**Key Migrations**:
- `0001_init.sql` - Initial schema
- `0016_add_extended_metrics_columns.sql` - Enhanced metrics tracking
- `0017_add_utm_tracking.sql` - UTM link tracking
- `0018_add_follower_tracking.sql` - Follower growth tracking
- `0020_add_content_analysis.sql` - AI performance analysis
- `0023_add_structured_campaign_brief.sql` - Structured brief support

**Apply Migrations**: Supabase automatically applies on deploy

---

**Document Maintained By**: Engineering Team
**Questions**: Refer to inline code comments or raise in team discussion
