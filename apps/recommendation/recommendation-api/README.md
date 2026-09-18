# recommendation-api

**Status: scaffold only — functionality not yet designed.**

## Purpose (as discussed so far)

Backend for the Recommendation component — the bridge between CoClub (SME
side) and Influencer. Matches/recommends influencers to SMEs (and vice versa,
TBD). Exact logic not yet designed.

## Data ownership

**No database of its own for now** — reads the influencer list directly from
`../../influencer/influencer-api`'s Supabase project. A deliberate early shortcut (tighter
coupling than going through `influencer-api`'s own HTTP endpoints instead) —
worth revisiting if `influencer-api`'s schema becomes fluid later. If this
component ever needs to store its own data (e.g. cached/precomputed matches),
it gets its own database at that point rather than writing into either other
component's tables.

## Relationship to other components

- Reads from `influencer-api`'s database (see above).
- May read from CoClub's `sme-api` too, once it's decided what SME-side data a
  recommendation actually needs (campaign requirements, brand niche, etc.) —
  not yet designed.
- `recommendation-web` is this service's frontend.

## Not yet done

Everything — this is a placeholder. No FastAPI app, no Dockerfile, no
dependencies, no docker-compose entry.
