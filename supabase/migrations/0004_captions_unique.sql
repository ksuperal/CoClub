-- Fixes duplicate caption rows: a race condition (concurrent POST /generate-copy
-- calls — e.g. React StrictMode's double-invoked effects in dev) could pass the
-- application-level "do captions already exist?" check before either request
-- finished writing, so both proceeded to insert a full set. Only a DB-level
-- constraint closes this reliably, since Postgres enforces it atomically no
-- matter how many concurrent requests arrive.

-- Clean up existing duplicates first (keeps the most recently generated row per
-- variant+platform, drops earlier ones) so the unique constraint below can be added.
delete from captions a using captions b
where a.variant_id = b.variant_id
  and a.platform = b.platform
  and a.created_at < b.created_at;

alter table captions
  add constraint captions_variant_platform_unique unique (variant_id, platform);
