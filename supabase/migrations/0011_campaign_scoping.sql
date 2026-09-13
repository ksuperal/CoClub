-- ---------------------------------------------------------------------------
-- Conversational campaign scoping — replaces the old fixed intake-form fields
-- (variant_count / media_type / include_voiceover / include_music, picked by
-- the user upfront with no context) with a short chat where the user
-- describes the campaign's size in their own words ("IG 9 posts, TikTok 2
-- short videos") and Claude turns that into a concrete, heterogeneous plan.
-- Those old campaign-level columns stay in place as a fallback default for
-- any campaign that somehow skips scoping — not dropped, just superseded.
-- ---------------------------------------------------------------------------

alter type campaign_status add value if not exists 'awaiting_scope';

-- scope_conversation: the back-and-forth transcript so far, [{role, text}, ...] —
-- lets the scoping chat resume correctly if the user navigates away mid-conversation.
alter table campaigns add column if not exists scope_conversation jsonb not null default '[]'::jsonb;

-- content_plan: the finalized plan once scoping is done — a jsonb array of
-- {media_type, target_platforms, count, include_voiceover, include_music, notes}
-- groups. ideate_variants expands each group into `count` individual variant rows.
-- Null until scoping finalizes; null forever means this campaign fell back to the
-- old uniform variant_count/media_type behavior.
alter table campaigns add column if not exists content_plan jsonb;

-- Which platform(s) this specific variant is for — empty means "no restriction,
-- post to every connected platform" (the pre-scoping behavior, and the fallback
-- for any variant not created from a content_plan). Step 3 only writes captions
-- for a variant's target_platforms when non-empty; Step 4 posts wherever a
-- caption exists, so it needs no separate change to respect this.
alter table variants add column if not exists target_platforms text[] not null default '{}';
