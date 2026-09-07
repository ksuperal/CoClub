-- CoClub MVP schema
-- Every table is scoped to auth.uid() via RLS. The FastAPI backend authenticates the
-- caller's Supabase JWT first, then writes with the service-role key on that user's behalf.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- brands
-- ---------------------------------------------------------------------------
create table if not exists brands (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  guideline_raw_text text,
  guideline_assets jsonb not null default '[]'::jsonb,   -- storage paths in brand-assets bucket
  extracted_profile jsonb,                                 -- Step 1 output: colors/tone/do-dont + citations
  created_at timestamptz not null default now()
);

alter table brands enable row level security;

create policy "brands_owner_all" on brands
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- campaigns
-- ---------------------------------------------------------------------------
create type campaign_type as enum (
  'product_launch', 'event_announcement', 'promo_offer', 'brand_awareness', 'other'
);

create type campaign_status as enum (
  'draft', 'generating_variants', 'awaiting_approval', 'approved',
  'posting', 'posted', 'awaiting_feedback', 'completed', 'failed'
);

create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  brand_id uuid not null references brands(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  campaign_type campaign_type not null,
  brief text not null,
  variant_count int not null default 4 check (variant_count between 1 and 10),
  status campaign_status not null default 'draft',
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table campaigns enable row level security;

create policy "campaigns_owner_all" on campaigns
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- variants
-- ---------------------------------------------------------------------------
create type variant_status as enum ('pending', 'approved', 'rejected');
create type quality_check_status as enum ('pending', 'passed', 'failed_max_retries');

create table if not exists variants (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  message_angle text not null,
  image_prompt text not null,
  image_url text,
  quality_check_status quality_check_status not null default 'pending',
  quality_check_attempts int not null default 0,
  quality_check_notes text,
  status variant_status not null default 'pending',
  created_at timestamptz not null default now()
);

alter table variants enable row level security;

create policy "variants_owner_all" on variants
  for all using (
    auth.uid() = (select user_id from campaigns where campaigns.id = variants.campaign_id)
  ) with check (
    auth.uid() = (select user_id from campaigns where campaigns.id = variants.campaign_id)
  );

-- ---------------------------------------------------------------------------
-- captions
-- ---------------------------------------------------------------------------
create table if not exists captions (
  id uuid primary key default gen_random_uuid(),
  variant_id uuid not null references variants(id) on delete cascade,
  platform text not null,   -- instagram | tiktok | youtube | facebook
  caption_text text not null,
  hashtags text[] not null default '{}',
  created_at timestamptz not null default now()
);

alter table captions enable row level security;

create policy "captions_owner_all" on captions
  for all using (
    auth.uid() = (
      select c.user_id from campaigns c
      join variants v on v.campaign_id = c.id
      where v.id = captions.variant_id
    )
  ) with check (
    auth.uid() = (
      select c.user_id from campaigns c
      join variants v on v.campaign_id = c.id
      where v.id = captions.variant_id
    )
  );

-- ---------------------------------------------------------------------------
-- posts
-- ---------------------------------------------------------------------------
create type post_status as enum ('pending_credentials', 'pending', 'posted', 'failed');

create table if not exists posts (
  id uuid primary key default gen_random_uuid(),
  variant_id uuid not null references variants(id) on delete cascade,
  platform text not null,
  external_post_id text,
  permalink text,
  status post_status not null default 'pending',
  posted_at timestamptz,
  error_message text,
  created_at timestamptz not null default now()
);

alter table posts enable row level security;

create policy "posts_owner_all" on posts
  for all using (
    auth.uid() = (
      select c.user_id from campaigns c
      join variants v on v.campaign_id = c.id
      where v.id = posts.variant_id
    )
  ) with check (
    auth.uid() = (
      select c.user_id from campaigns c
      join variants v on v.campaign_id = c.id
      where v.id = posts.variant_id
    )
  );

-- ---------------------------------------------------------------------------
-- post_metrics
-- ---------------------------------------------------------------------------
create table if not exists post_metrics (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references posts(id) on delete cascade,
  likes int not null default 0,
  comments int not null default 0,
  shares int not null default 0,
  views int not null default 0,
  fetched_at timestamptz not null default now()
);

alter table post_metrics enable row level security;

create policy "post_metrics_owner_all" on post_metrics
  for all using (
    auth.uid() = (
      select c.user_id from campaigns c
      join variants v on v.campaign_id = c.id
      join posts p on p.variant_id = v.id
      where p.id = post_metrics.post_id
    )
  ) with check (
    auth.uid() = (
      select c.user_id from campaigns c
      join variants v on v.campaign_id = c.id
      join posts p on p.variant_id = v.id
      where p.id = post_metrics.post_id
    )
  );

-- ---------------------------------------------------------------------------
-- campaign_reports
-- ---------------------------------------------------------------------------
create table if not exists campaign_reports (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  summary_text text not null,
  top_variant_id uuid references variants(id),
  verdicts jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

alter table campaign_reports enable row level security;

create policy "campaign_reports_owner_all" on campaign_reports
  for all using (
    auth.uid() = (select user_id from campaigns where campaigns.id = campaign_reports.campaign_id)
  ) with check (
    auth.uid() = (select user_id from campaigns where campaigns.id = campaign_reports.campaign_id)
  );

-- ---------------------------------------------------------------------------
-- usage_events — groundwork for future token-based billing
-- ---------------------------------------------------------------------------
create table if not exists usage_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  campaign_id uuid references campaigns(id) on delete set null,
  kind text not null,          -- 'llm_call' | 'image_gen'
  units int not null default 0,   -- tokens for llm_call, image count for image_gen
  cost_estimate numeric(10, 4),
  created_at timestamptz not null default now()
);

alter table usage_events enable row level security;

create policy "usage_events_owner_all" on usage_events
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- ---------------------------------------------------------------------------
-- storage bucket for brand assets
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('brand-assets', 'brand-assets', false)
on conflict (id) do nothing;

create policy "brand_assets_owner_read" on storage.objects
  for select using (bucket_id = 'brand-assets' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "brand_assets_owner_write" on storage.objects
  for insert with check (bucket_id = 'brand-assets' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "brand_assets_owner_delete" on storage.objects
  for delete using (bucket_id = 'brand-assets' and auth.uid()::text = (storage.foldername(name))[1]);

-- ---------------------------------------------------------------------------
-- storage bucket for generated variant images — public read, since Step 4
-- posting (Ayrshare) needs a publicly fetchable mediaUrl. Writes still go
-- through the backend's service-role key, path-prefixed by user_id.
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('campaign-variants', 'campaign-variants', true)
on conflict (id) do nothing;

create policy "campaign_variants_public_read" on storage.objects
  for select using (bucket_id = 'campaign-variants');

create policy "campaign_variants_owner_write" on storage.objects
  for insert with check (bucket_id = 'campaign-variants' and auth.uid()::text = (storage.foldername(name))[1]);

-- keep campaigns.updated_at fresh
create or replace function set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger campaigns_set_updated_at
  before update on campaigns
  for each row execute function set_updated_at();
