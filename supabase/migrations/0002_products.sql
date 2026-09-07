-- Product intake: mirrors brand intake (upload + optional text -> structured profile),
-- but the upload is required since the product photo is the primary reference for
-- generating visually-accurate ad creative.

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  brand_id uuid not null references brands(id) on delete cascade,
  name text not null,
  description_text text,
  asset_paths jsonb not null default '[]'::jsonb,
  extracted_profile jsonb,   -- { category, key_features, selling_points, visual_description, citations }
  created_at timestamptz not null default now()
);

alter table products enable row level security;

create policy "products_owner_all" on products
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- campaigns can optionally target a specific product
alter table campaigns add column if not exists product_id uuid references products(id) on delete set null;

-- ---------------------------------------------------------------------------
-- storage bucket for product photos/files — private, same pattern as brand-assets
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('product-assets', 'product-assets', false)
on conflict (id) do nothing;

create policy "product_assets_owner_read" on storage.objects
  for select using (bucket_id = 'product-assets' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "product_assets_owner_write" on storage.objects
  for insert with check (bucket_id = 'product-assets' and auth.uid()::text = (storage.foldername(name))[1]);

create policy "product_assets_owner_delete" on storage.objects
  for delete using (bucket_id = 'product-assets' and auth.uid()::text = (storage.foldername(name))[1]);
