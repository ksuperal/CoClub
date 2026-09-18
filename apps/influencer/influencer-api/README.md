# influencer-api

**Status: scaffold only — functionality not yet designed.**

## Purpose (as discussed so far)

Backend for the Influencer component — the second of three components in this
system (alongside CoClub's existing `sme-api`/`sme-web`, and `recommendation-api`/
`recommendation-web`). Intended to hold the core of the network effect: a list of
influencers and their attributes. Exact data model and features TBD.

## Data ownership

This service gets **its own Supabase project** (own database), separate from
CoClub's (`../../../supabase/`). Not a shared schema — a genuinely separate project,
so this component owns its data independently. Migrations for it belong in
`supabase/migrations/` in this folder, same convention as CoClub's own.

## Relationship to other components

- `recommendation-api` reads influencer data from this service's database
  directly (not yet decided whether that stays a direct DB connection or moves
  to going through this service's own HTTP endpoints instead — noted as a
  deliberate early shortcut, not a final decision).
- Shares Supabase Auth as the identity provider with CoClub and Recommendation
  (one login across all three), per the architecture review's recommendation —
  not yet wired up.

## Not yet done

Everything — this is a placeholder. No FastAPI app, no Dockerfile, no
dependencies, no docker-compose entry. Follow `apps/sme/sme-api`'s existing shape
(`app/main.py`, `app/config.py`, `app/db.py`, `requirements.txt`, `Dockerfile`)
once real functionality is scoped.
