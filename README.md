# CoClub

AI-powered marketing platform for SMEs — an alternative to hiring/relying on a marketing
agency. Turns brand assets + a campaign brief into approved, published, multi-platform ad
campaigns through a 5-step pipeline.

## Pipeline

1. **Brand intake** — upload brand guideline + assets, describe the campaign
2. **Variant generation** — AI generates message angles → image prompts → ad images
   (with a vision-based brand-compliance quality check loop)
3. **Copywriting** — captions + hashtags per platform
4. **Approve & post** — after user approval, posts directly to Facebook/Instagram/TikTok via
   each platform's native API; accounts that aren't connected yet fall back to `pending_credentials`
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

Create a Supabase project. Run the SQL in `supabase/migrations/0001_init.sql` in the
Supabase SQL editor (or via `supabase db push` if using the CLI). This creates all tables,
enables RLS, and adds a `brand-assets` storage bucket.

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

### 3. Frontend (`apps/web`)

```bash
cd apps/web
npm install
cp .env.example .env.local   # fill in keys
npm run dev
```

Open http://localhost:3000.

## Environment variables

| Var | Where | Required for MVP | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | api | yes | Claude — extraction, copywriting, quality-check, reports |
| `OPENAI_API_KEY` | api | yes | `gpt-image-2` — ad image generation |
| `SUPABASE_URL` | api, web | yes | |
| `SUPABASE_ANON_KEY` | web | yes | used by the browser client for auth |
| `SUPABASE_SERVICE_ROLE_KEY` | api | yes | backend writes, bypasses RLS after verifying the caller's JWT |
| `META_APP_ID` / `META_APP_SECRET` / `META_REDIRECT_URI` | api | no | Facebook Login for Business app — covers both Facebook Page and Instagram posting. See "Social posting setup" below |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REDIRECT_URI` | api | no | TikTok Content Posting API app. See "Social posting setup" below |
| `SOCIAL_TOKEN_ENCRYPTION_KEY` | api | only if connecting accounts | encrypts stored account tokens at rest; generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `FRONTEND_URL` | api | no | where the OAuth callback redirects the browser back to; defaults to `http://localhost:3000` |

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
`draft → generating_variants → awaiting_approval → approved → posting → posted → awaiting_feedback → completed`
(or `failed` from any step).

## Notes on scope

This is the first MVP. Steps 1–3 and the quality-check loop are fully real (real LLM +
image-gen calls). Step 4 posting is real but gated on each user connecting their own
accounts under `/settings/social` — without a connected account for a platform, the
pipeline still runs end-to-end and that platform's posts sit as `pending_credentials`.
TikTok posting additionally stays private/draft-only until the TikTok app clears audit
(see "Social posting setup" above) — this is a platform-side gate, not a bug. Usage is
logged per LLM/image-gen call to `usage_events` now so token-based billing can be added
later without re-instrumenting anything.


Feat-
Message-
Fix-
Bug-