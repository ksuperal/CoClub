-- Step 4 posting moves from Ayrshare (third-party aggregator) to direct platform APIs.
-- Each connected account is one row: a Meta OAuth grant can produce up to two rows
-- (facebook + instagram) since IG posting piggybacks on the linked Page's access token.

create type social_account_status as enum ('connected', 'expired', 'revoked');

create table if not exists social_accounts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  platform text not null,                  -- facebook | instagram | tiktok
  external_account_id text not null,       -- page_id (facebook) / ig_user_id (instagram) / open_id (tiktok)
  external_account_name text,              -- display name/username for the connect-accounts UI
  platform_metadata jsonb not null default '{}'::jsonb,  -- e.g. {"page_id": "..."} on the instagram row
  access_token_encrypted text not null,
  refresh_token_encrypted text,            -- tiktok only
  token_expires_at timestamptz,            -- tiktok only; meta page tokens don't expire under normal use
  status social_account_status not null default 'connected',
  connected_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, platform)
);

alter table social_accounts enable row level security;

create policy "social_accounts_owner_all" on social_accounts
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- reuses the set_updated_at() function defined in 0001_init.sql
create trigger social_accounts_set_updated_at
  before update on social_accounts
  for each row execute function set_updated_at();
