-- Add per-variant reference asset
-- Users can upload a single style reference image for each variant during ideation.
-- These are stored separately from brand/product assets and used alongside them
-- during image generation to preserve specific visual styles.

ALTER TABLE variants
ADD COLUMN reference_asset TEXT DEFAULT NULL;

COMMENT ON COLUMN variants.reference_asset IS 'Optional Supabase storage path for a single style reference image uploaded specifically for this variant during prompt review';
