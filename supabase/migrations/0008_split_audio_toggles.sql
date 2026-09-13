-- Splits the single "include_audio" toggle into two independent ones — a user
-- may want voiceover narration without a music bed, or a music bed without
-- narration, not only "both or neither".
alter table campaigns add column if not exists include_voiceover boolean not null default false;
alter table campaigns add column if not exists include_music boolean not null default false;

-- No real customer data depends on the old combined flag yet (this project isn't
-- launched) — drop it outright rather than carry a superseded column forward.
alter table campaigns drop column if exists include_audio;
