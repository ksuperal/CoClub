# CoClub

AI-powered marketing platform for SMEs — an alternative to hiring/relying on a marketing
agency. Turns brand assets + a campaign brief into approved, published, multi-platform ad
campaigns through a 5-step pipeline.

## Pipeline

1. **Brand intake** — upload brand guideline + assets, describe the campaign
2. **Variant generation** — AI generates message angles → image prompts → ad images
   (with a vision-based brand-compliance quality check loop)
3. **Copywriting** — captions + hashtags per platform
4. **Approve & post** — after user approval, posts to IG/TikTok/YouTube/FB via Ayrshare
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
| `AYRSHARE_API_KEY` | api | no | leave unset — Step 4 posting will mark posts `pending_credentials` until this is set |

## Status model

`campaigns.status` moves through:
`draft → generating_variants → awaiting_approval → approved → posting → posted → awaiting_feedback → completed`
(or `failed` from any step).

## Notes on scope

This is the first MVP. Steps 1–3 and the quality-check loop are fully real (real LLM +
image-gen calls). Step 4 posting is real but gated on having an Ayrshare account — without
one, the pipeline still runs end-to-end and posts sit as `pending_credentials`. Usage is
logged per LLM/image-gen call to `usage_events` now so token-based billing can be added
later without re-instrumenting anything.
