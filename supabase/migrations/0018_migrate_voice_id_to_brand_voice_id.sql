-- Migrate voice_id to brand_voice_id
--
-- Migration 0012 added brand_voice_id for the brand library feature, but the code
-- was never updated to use it. This migration backfills brand_voice_id with
-- existing voice_id values so all brands use the new field consistently.

-- Copy existing voice_id values to brand_voice_id
UPDATE brands
SET brand_voice_id = voice_id
WHERE brand_voice_id IS NULL AND voice_id IS NOT NULL;

-- Update comment to clarify voice_id is deprecated
COMMENT ON COLUMN brands.voice_id IS
'DEPRECATED: Use brand_voice_id instead. Kept for backward compatibility only.';
