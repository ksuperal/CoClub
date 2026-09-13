# Migrating CoClub toward an agent interface

**Status: planned, not started.** This document exists so the idea doesn't have to be
re-derived later — nothing here is implemented. Triggered by evaluating Higgsfield
Supercomputer (a chat-driven creative agent) and asking whether CoClub's own
architecture could grow the same capability without adopting their product.

## Decisions already made (don't re-litigate these)

- **The fixed 5-step wizard stays the primary flow for the MVP.** This plan adds an
  agent as an *additional* entry point, not a replacement. The wizard's explicit
  review-before-spend checkpoints are a deliberate strength, not a gap.
- **No scheduled/recurring agent-triggered campaigns in this phase.** Not needed yet.
- **No new connectors (Slack/Drive/Gmail/etc.) in this phase.** The social platform
  connectors already built are sufficient.
- **Multi-model routing:** near-term, just add an audio generation model/API
  alongside the existing image/video ones (see `TODO.md`). OpenRouter-based dynamic
  model routing is a separate, later idea — not part of this plan.
- **Upfront credit/cost estimates** (shown before a spend, like Supercomputer does)
  are a separate future iteration, tracked in `TODO.md` — not required to ship
  Phase 1 below.

## What "agent" means here

A chat interface where a user describes what they want in free text, and Claude
plans which of CoClub's existing pipeline steps to call — instead of clicking
through the wizard's fixed screens. Concretely: today's pipeline functions
(`ideate_variants`, `generate_variant_media`, `run_copywriting`,
`approve_campaign`, `post_campaign`, `refresh_metrics`, ...) become **tools** an
agent can invoke, on top of a multi-turn tool-use loop instead of today's
single-forced-tool-call pattern (`llm._forced_tool_call`).

Grounded in Anthropic's current Tool Runner pattern (`client.beta.messages.tool_runner`,
Python SDK, beta) — see the `claude-api` skill's `shared/tool-use-concepts.md` and
`python/claude-api/tool-use.md`. Key fact that makes this safe to build: **the
runner supports human-in-the-loop approval gates natively** — a tool's own run
function can return a "needs confirmation" result instead of executing, or the
caller can intercept a pending tool call via `runner.set_messages_params()` before
it runs. This is exactly the "review before spend" pattern the wizard already
uses (ideate → review prompts → generate; approve → post) — the agent version
just expresses it conversationally instead of as a separate screen, it doesn't
abandon it.

## Phase 0 — Schema

New tables (own migration, RLS following the existing `user_id`-ownership pattern
every other table here uses):

```sql
create table agent_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text,                          -- first user message, truncated, for a history list
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table agent_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references agent_conversations(id) on delete cascade,
  role text not null,                  -- 'user' | 'assistant' | 'tool_result'
  content jsonb not null,              -- raw Claude content blocks — replayed verbatim on resume
  created_at timestamptz not null default now()
);
```

Storing raw content blocks (not just extracted text) matters — tool_use/tool_result
blocks must round-trip exactly for the conversation to resume correctly, same
reason `services/scheduler.py`'s job persistence stores enough to reconstruct state
after a restart.

**Model choice:** default to `claude-sonnet-5` (matches every other LLM call in
this codebase already — `config.py`'s `anthropic_model` default) rather than
reaching for Opus by default. Revisit only if real usage shows the agent's
multi-step planning is the bottleneck, not preemptively.

## Phase 1 — Tool surface (`services/agent_tools.py`, new)

Thin `@beta_tool`-decorated wrappers around **existing** pipeline functions — no
pipeline logic gets duplicated, each tool just adapts the existing function's
signature/return shape for the agent loop and trims the response to what's
context-cheap (summaries, not full raw rows).

| Tool | Wraps | Gate? |
|---|---|---|
| `list_brands`, `get_brand`, `list_campaigns`, `get_campaign` | existing read endpoints | No — read-only |
| `create_brand` | `routers/brands.py` create logic | No — cheap, reversible |
| `create_campaign` | campaign creation | No — cheap, reversible |
| `ideate_variants` | `step2_variants.ideate_variants` | No — LLM-only, no media-gen cost |
| `update_variant_prompt` | existing PATCH endpoint logic | No — cheap, reversible |
| **`generate_variant_media`** | `step2_variants.generate_variant_media` | **Yes** — real image-gen/video-gen spend |
| `generate_copy` | `step3_copywriting.run_copywriting` | No — LLM-only |
| `approve_campaign` | `step4_approve_post.approve_campaign` | No direct cost — commits selection, not spend |
| **`post_campaign`** | `step4_approve_post.post_campaign` | **Yes** — irreversible, posts live to real accounts |
| `refresh_metrics`, `get_metrics_history`, `get_posting_time_recommendation` | existing Step 5 functions | No — read-only |

Only two tools need a real approval gate — everything else is already cheap or
reversible today, same as it is in the wizard.

## Phase 2 — Approval gate mechanism

For `generate_variant_media` and `post_campaign`: the tool function's first call
(no `confirmed` argument, or `confirmed=false`) does **not** execute — it returns a
structured summary of what would happen (variant count, estimated cost range once
the cost-estimate TODO item lands, which platforms would receive a post) and asks
Claude to relay that to the user and wait for an explicit yes. Only a follow-up
call with `confirmed=true` — which the agent only emits after the user's next
message reads as approval — actually runs the underlying pipeline function.

Belt-and-suspenders, matching how the duplicate-caption bug was ultimately fixed
earlier in this project (app-level check + DB-level constraint, not one alone): in
addition to the tool's own internal gate, the conversation loop itself inspects
each yielded message for a pending call to one of the two gated tools and uses
`runner.set_messages_params()` to hold it rather than trusting the tool function's
internal check as the only safeguard.

## Phase 3 — Backend (`routers/agent.py`, new)

- `POST /agent/conversations` — start a new conversation, returns its id.
- `POST /agent/conversations/{id}/messages` — send a user message, run the tool
  loop (`client.beta.messages.tool_runner(...)`), persist every turn to
  `agent_messages`, return the assistant's response (including any pending
  confirmation the frontend should render specially).
- `GET /agent/conversations/{id}` — resume: replay stored `agent_messages` content
  blocks back into a fresh runner call.

## Phase 4 — Frontend (`/agent`, new page)

Simple chat UI — message list, input box. A pending-confirmation turn renders as a
distinct card with explicit **Approve / Cancel** buttons (not free text) so
confirmation parsing is unambiguous, not "did the user's next message count as a
yes." Existing wizard pages (`/intake`, `/campaign/[id]/prompts`, `/campaign/[id]/variants`,
`/campaign/[id]`) are untouched and stay the default flow.

## Phase 5 — Skills (optional, smaller, do last)

The lightweight version of Supercomputer's "skills": a plain Python dict mapping a
short name (e.g. `"regenerate_variant"`) to a canned multi-tool-call instruction the
agent expands, rather than a new DB-backed registry. Defer until the base loop from
Phases 0–4 is proven out — no reason to build a skills abstraction before there's a
working agent to hang it off.

## Open risks, stated plainly

- **Tool Runner is beta** (`client.beta.messages.tool_runner`) — first beta
  dependency in this codebase; every other LLM call here uses the stable
  `messages.create`. API surface can shift under a beta.
- **Cost per interaction is higher than today's flow** — a chat turn can trigger
  several tool round-trips (each a real LLM call) where the wizard's forced-single-
  tool-call pattern costs exactly one. Worth measuring before wide rollout, not
  assuming it's fine.
- **RLS/ownership** on the two new tables must follow the same `user_id`-scoped
  policy pattern as every other table (`campaigns_owner_all` etc.) — a new surface
  is a new place to get that wrong.

## Verification approach (once actually started)

Same discipline used for the video-generation feature: compile-check + boot-check
after each phase, then a real (cheap) test conversation exercising one
auto-executing tool and one gated tool, explicitly confirming the gate blocks
execution without an approval turn — not just that it eventually runs when
approved.

## Critical files (once started)

- New migration — schema above
- `apps/api/app/services/agent_tools.py` (new)
- `apps/api/app/routers/agent.py` (new)
- `apps/web/app/agent/page.tsx` (new)
- Existing pipeline functions in `apps/api/app/pipeline/*.py` — read, not modified;
  the whole point is these stay the single source of truth for pipeline logic.
