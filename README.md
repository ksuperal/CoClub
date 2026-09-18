# CoClub

AI-powered marketing platform for SMEs — an alternative to hiring/relying on a marketing
agency. Turns a brand + a campaign brief into approved, published, multi-platform ad
campaigns through a conversational scoping step and a 5-step pipeline.

## Pipeline

0. **Brand & Product Library** — brands and products are reusable presets, not
   re-entered per campaign. Create a brand once (`/brands/new` — guideline text/files →
   an extracted brand profile, plus an ElevenLabs voice picked for it) or a product once
   (`/products/new` — photos/description → an extracted product profile), then reuse
   either across as many campaigns as you like from `/intake`. Brands can be edited
   (`/brands/[id]/edit`) or archived (soft-delete — existing campaigns keep their
   reference).
1. **Campaign scoping** (conversational, `/campaign/[id]/scope`) — describe the
   campaign's size and shape in your own words ("IG 9 posts, TikTok 2 short videos")
   instead of picking fields from a form. Claude asks follow-ups until it has enough to
   propose a concrete, heterogeneous **content plan** — per item: media type, target
   platform(s), count, whether it needs a voiceover, and a real creative concept (shot/
   scene description, not just a format). It's aware of which platforms you've actually
   connected (flags one you haven't), reaches for capped web research only when you seem
   unsure rather than by default, and can take moodboard/reference images uploaded mid-
   conversation into account. Nothing is generated yet — you confirm the plan before any
   cost is spent.
2. **Variant generation** — split into two calls so nothing expensive runs unreviewed:
   - **Ideate** — from the confirmed plan, AI writes message angles → image prompts
     (and, for video items, a motion prompt + voiceover script + music prompt too). A
     plan item can also carry a reference image to replicate its exact shot composition.
     No image-gen/video-gen/audio-gen cost yet.
   - **Review & generate** (`/campaign/[id]/prompts`) — edit or skip any prompt, then
     generate real media only for what's kept: images via `gpt-image-2` (with a
     vision-based brand-compliance quality-check loop), video via that same starting
     image animated through Luma's Ray image-to-video model, background music
     (mandatory for every video piece) and voiceover (only if asked for) via ElevenLabs,
     muxed onto the video with `ffmpeg`.
3. **Copywriting** — captions + hashtags per platform, written for that platform's own
   norms (Instagram: hook-first + hashtag mix; TikTok: ultra-short + curiosity hook;
   Facebook: longer-form, community tone) — only for the platforms a variant actually
   targets.
4. **Approve & post** — after user approval, posts directly to Facebook/Instagram/TikTok via
   each platform's native API (video variants post as native video — Instagram Reels,
   TikTok video, Facebook video); accounts that aren't connected yet fall back to
   `pending_credentials`
5. **Feedback** — 24 hours later, a report on what's worth boosting

## Structure

```
apps/
  api/        FastAPI backend — the pipeline lives here
  web/        Next.js frontend — minimal UI to drive the pipeline
supabase/
  migrations/ Postgres schema + RLS policies
```

## Setup

### 1. Supabase

Create a Supabase project. Run every file in `supabase/migrations/` **in order**
(`0001_init.sql` through the latest) in the Supabase SQL editor, or via `supabase db
push` if using the CLI — each one is a small, additive step (schema changes, RLS
policies, storage buckets) rather than one big init script now. This creates all
tables, enables RLS, and adds the `brand-assets` and `product-assets` storage buckets
(moodboard and variant-reference images also live in `brand-assets`).

### 2. Backend (`apps/api`)

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # fill in keys
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

The data API (brands/products/campaigns/reports/assets) is versioned under `/v1/...`
(e.g. `/v1/brands`) — a stable contract for a future second/third component to build
against. `/social/...` (OAuth connect/callback routes) and `/health` stay unversioned
deliberately: two of the social routes are OAuth redirect URIs already registered in
the Meta/TikTok developer dashboards, so versioning them would break those live
integrations. A committed snapshot of the current schema lives at
`apps/api/openapi.json` — regenerate it after any route change with `cd apps/api &&
python scripts/export_openapi.py`.

### 3. Frontend (`apps/web`)

```bash
cd apps/web
npm install
cp .env.example .env.local   # fill in keys
npm run dev
```

Open http://localhost:3000.

### 4. Or: Docker Compose

Once `apps/api/.env` and `apps/web/.env.local` are filled in (step 1 still applies --
Supabase itself isn't containerized, it stays the hosted project):

```bash
docker compose up --build
```

Same two apps (http://localhost:8000, http://localhost:3000), containerized. Set
`NEXT_PUBLIC_API_URL`/`CORS_ALLOW_ORIGINS` env vars before `up` if the API isn't at the
default `http://localhost:8000`.

### Tests

```bash
cd apps/api
pip install -r requirements-dev.txt
pytest tests -v
```

Currently covers tenant isolation (a user can never read/write another user's brand or
campaign) and the local JWT / service-key auth paths added above -- run against an
in-memory fake of the Supabase client (`tests/conftest.py`), no real Supabase project
needed.

## Environment variables

| Var | Where | Required for MVP | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | api | yes | Claude — extraction, copywriting, quality-check, reports |
| `OPENAI_API_KEY` | api | yes | `gpt-image-2` — ad image generation |
| `SUPABASE_URL` | api, web | yes | |
| `SUPABASE_ANON_KEY` | web | yes | used by the browser client for auth |
| `SUPABASE_SERVICE_ROLE_KEY` | api | yes | backend writes, bypasses RLS after verifying the caller's JWT |
| `SUPABASE_JWT_SECRET` | api | no | verifies the caller's JWT locally instead of a round-trip to Supabase Auth on every request; only works for a project still on the legacy shared JWT secret (newer asymmetric-signing-key projects should leave this unset, which falls back to the live Supabase Auth call) |
| `CORS_ALLOW_ORIGINS` | api | no | comma-separated browser origins allowed to call this API; defaults to `http://localhost:3000` |
| `SERVICE_API_KEYS` | api | no | comma-separated shared keys for machine-to-machine callers via `X-Service-Key`; unused until a second/third component actually calls in with one |
| `DATABASE_URL` | api, worker | no | Postgres connection string for the durable scheduler job store (video polling, metrics polling, the feedback job, media generation). Without it, jobs live in memory only, don't survive a restart, and the `api` process executes them itself — fine for local dev. **With** it set, the separate `worker` process becomes the one that actually runs jobs (`api` only enqueues them) — see "Background jobs" below |
| `META_APP_ID` / `META_APP_SECRET` / `META_REDIRECT_URI` / `META_LOGIN_CONFIG_ID` | api | no | Facebook Login for Business app — covers both Facebook Page and Instagram posting. See "Social posting setup" below |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REDIRECT_URI` | api | no | TikTok Content Posting API app. See "Social posting setup" below |
| `SOCIAL_TOKEN_ENCRYPTION_KEY` | api | only if connecting accounts | encrypts stored account tokens at rest; generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FRONTEND_URL` | api | no | where the OAuth callback redirects the browser back to; defaults to `http://localhost:3000` |
| `LUMA_API_KEY` | api | only for video campaigns | image-to-video generation (Step 2), via Luma's Ray model (Luma Agents API). API key from platform.lumalabs.ai. Without it, video campaigns still ideate/review normally but each variant's generation fails cleanly with `generation_status = 'failed'` instead of crashing |
| `ELEVENLABS_API_KEY` | api | no | voiceover and background music for video variants (Step 2) — background music is mandatory for every video piece, voiceover only if you say yes when the scoping conversation asks. Voiceover via `eleven_v3` (chosen for expressiveness over OpenAI TTS, which read as flat/monotone in testing), music via the Music API. The key needs four scopes enabled: Music Generation (Access), Text to Speech (Access), Voices (Read), and nothing else. Also requires the `ffmpeg` binary on PATH (system dependency, not pip) to mix/mux audio onto the video; without either, a video variant still generates, just silently without audio |

## Social posting setup

Step 4 posts directly to each platform's API — no third-party aggregator, no per-profile
fee. This needs two things outside this repo before real posting works, in addition to the
env vars above:

1. **Meta Developer App** (developers.facebook.com) — add the "Facebook Login for Business"
   product, request the `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
   `instagram_basic`, `instagram_content_publish`, and `business_management` permissions,
   complete Business Verification, and submit for App Review. Until reviewed, only accounts
   added as Testers/Admins on the app can complete the connect flow — that's expected during
   development, not a bug.
   **Also required:** under Facebook Login for Business → Configurations, create a Login
   Configuration with those same permissions and copy its ID into `META_LOGIN_CONFIG_ID` —
   without one, the OAuth dialog shows "App not active" even with everything else set up
   correctly (Facebook Login for Business grants permissions via a saved configuration, not
   a raw scope list).
2. **TikTok Developer App** (developers.tiktok.com) — add the Content Posting API product,
   request the `video.publish` scope (also covers photo posting — there's no separate photo
   scope), and submit for audit. Until audited, posts land as private/draft, visible only to
   the connecting account — public posting activates automatically once the audit clears, no
   code changes needed. Posting by URL (`PULL_FROM_URL`) also requires verifying the exact
   image storage path prefix in the TikTok developer dashboard.

**Account prerequisites for whoever is connecting** (surfaced in the `/settings/social` UI
too, but worth stating plainly): Facebook needs a **Page** (personal profiles can't be posted
to via the API at all); Instagram needs a **Business or Creator account linked to a Facebook
Page**; TikTok needs a **Business or Creator account** (personal TikTok accounts aren't
eligible for the Content Posting API). All three are free, quick account-settings changes —
not something this app can do on a user's behalf.

Register the exact redirect URIs (`META_REDIRECT_URI` / `TIKTOK_REDIRECT_URI`) in each
platform's dashboard. Both platforms require `https` redirect URIs — for local dev, tunnel
the API with a persistent tunnel (e.g. `devtunnel host <name>` after `devtunnel create <name>
--allow-anonymous`, or ngrok) and use that URL; a temporary/anonymous tunnel gets a new URL
every restart, which then has to be re-registered in both `.env` and each developer dashboard.

Users connect their own accounts from `/settings/social` in the web app — this drives the
OAuth flow in `apps/api/app/routers/social.py`, which stores encrypted tokens in the
`social_accounts` table (`apps/api/app/services/crypto.py`).

## Status model

`campaigns.status` moves through:
`draft → awaiting_scope → awaiting_prompt_review → generating_variants → awaiting_approval → approved → posting → posted → awaiting_feedback → completed`
(or `failed` from any step). `awaiting_scope` is the scoping conversation's checkpoint —
the campaign sits here across as many chat turns as it takes, with each finalized plan
overwriting the last, until `/scope/confirm` locks one in. `awaiting_prompt_review` is
the ideate/generate split's review checkpoint right after — variants exist with prompts
filled in but no media generated, no cost spent yet.

Each `variants` row also tracks its own `generation_status`
(`awaiting_prompt_review → generating → generated`, or `failed`) independently of the
campaign's status and of the variant's approve/reject `status` — a video variant in
particular can still be `generating` in the background (polled separately) after the
campaign has already moved on to `awaiting_approval`.

## Background jobs

Video polling, metrics polling, the 24h feedback job, and media generation
(image/video) all run through `apps/api/app/services/scheduler.py`, an APScheduler
instance backed by Postgres when `DATABASE_URL` is set.

- **`DATABASE_URL` unset** (default for local dev): the `api` process both enqueues
  and executes these itself, in-process — simplest setup, nothing else to run, but
  jobs don't survive an `api` restart and don't scale past one replica.
- **`DATABASE_URL` set**: `api` only *enqueues* jobs (its own scheduler starts paused
  and never executes anything) — a separate `worker` process (`apps/api/app/worker.py`,
  run with `python -m app.worker`, already wired up as its own service in
  `docker-compose.yml`) is what actually runs them, reading from the same Postgres
  jobstore. This is what makes it safe to eventually run more than one `api` replica —
  only the one worker process ever executes a given job, so nothing can fire twice.
  Outside Docker, run it yourself in a second terminal: `cd apps/api && uvicorn
  app.main:app --reload` in one, `python -m app.worker` in another, both pointed at
  the same `DATABASE_URL`.

## Notes on scope

This is the first MVP. Brand/Product Library, campaign scoping, and Steps 1–3 (plus the
image quality-check loop) are fully real — real LLM, image-gen, video-gen, and audio-gen
calls throughout, no mocked steps. Step 4 posting is real but gated on each user
connecting their own accounts under `/settings/social` — without a connected account for
a platform, the pipeline still runs end-to-end and that platform's posts sit as
`pending_credentials`. TikTok posting additionally stays private/draft-only until the
TikTok app clears audit (see "Social posting setup" above) — this is a platform-side
gate, not a bug. Usage is logged per LLM/image-gen/video-gen/audio-gen call to
`usage_events` so token-based billing can be added later without re-instrumenting
anything.

See `TODO.md` for what's open — known gaps, deferred design work, and housekeeping.