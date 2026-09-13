-- ---------------------------------------------------------------------------
-- Audio: voiceover (OpenAI gpt-4o-mini-tts) + background music (ElevenLabs
-- Music), mixed together and muxed onto the (already-generated, silent) video
-- via ffmpeg. Opt-in per campaign, only meaningful for media_type = 'video'.
-- ---------------------------------------------------------------------------

-- One voice per brand, chosen once from brand tone/guideline at intake time —
-- consistency across that brand's ads, like a real brand voice. Nullable: falls
-- back to a sensible default at generation time for brands created before this
-- migration (or if voice selection itself ever fails).
alter table brands add column if not exists voice_id text;

-- Opt-in per campaign — audio only makes sense alongside video, but the UI (not
-- this constraint) is responsible for only offering it when media_type = 'video'.
alter table campaigns add column if not exists include_audio boolean not null default false;

-- Per-variant, LLM-written during ideation (same review-before-spend checkpoint
-- as image_prompt/motion_prompt) — a short spoken script distinct from the
-- written social caption, a tone direction for delivery, and a music style
-- description.
alter table variants add column if not exists voiceover_script text;
alter table variants add column if not exists voice_instructions text;
alter table variants add column if not exists music_prompt text;

-- Non-fatal: if audio generation/mixing fails, the variant still ships with its
-- silent video rather than blocking the whole campaign — this records why, for
-- the UI to surface as a soft warning, not a blocker.
alter table variants add column if not exists audio_gen_error text;
