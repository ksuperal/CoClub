-- ---------------------------------------------------------------------------
-- Video generation support: media type + video-specific fields on variants,
-- plus a generation lifecycle distinct from the existing approval `status`
-- (approved/rejected is about posting; generation_status is about whether
-- media has been generated yet).
-- ---------------------------------------------------------------------------

alter table variants add column if not exists media_type text not null default 'image'; -- 'image' | 'video'
alter table variants add column if not exists motion_prompt text;          -- video only
alter table variants add column if not exists video_url text;
alter table variants add column if not exists generation_status text not null default 'generated';
  -- 'awaiting_prompt_review' | 'generating' | 'generated' | 'failed'
  -- existing rows default to 'generated' — they already have media, nothing to review
alter table variants add column if not exists video_gen_job_id text;       -- Higgsfield request_id, for polling
alter table variants add column if not exists video_gen_error text;

alter table variants add constraint variants_media_type_check
  check (media_type in ('image', 'video'));

alter table variants add constraint variants_generation_status_check
  check (generation_status in ('awaiting_prompt_review', 'generating', 'generated', 'failed'));

-- campaigns: new status between draft and generating_variants, plus the
-- campaign-level toggle deciding what ideate_variants produces for every variant.
alter type campaign_status add value if not exists 'awaiting_prompt_review';
alter table campaigns add column if not exists media_type text not null default 'image'; -- 'image' | 'video'
alter table campaigns add constraint campaigns_media_type_check
  check (media_type in ('image', 'video'));
