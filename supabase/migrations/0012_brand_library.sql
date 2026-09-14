-- Brand Library: Add brand preset fields for reusability across campaigns
--
-- This migration enables brand presets that can be reused across multiple campaigns,
-- eliminating the need to re-upload brand guidelines and re-extract brand profiles
-- every time a new campaign is created.

-- Add description field for brand background/context
ALTER TABLE brands
ADD COLUMN description TEXT;

-- Add consistent brand voice for all campaigns using this brand
ALTER TABLE brands
ADD COLUMN brand_voice_id TEXT;

-- Add index for faster brand lookups by user
CREATE INDEX IF NOT EXISTS idx_brands_user_id_created
ON brands(user_id, created_at DESC);

-- Add comment explaining the brand voice field
COMMENT ON COLUMN brands.brand_voice_id IS
'ElevenLabs voice ID selected once for this brand, used consistently across all campaigns';

COMMENT ON COLUMN brands.description IS
'High-level description of the brand for context (industry, positioning, target audience)';
