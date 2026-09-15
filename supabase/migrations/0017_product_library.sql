-- Product Library: Add product preset fields for reusability across campaigns
--
-- This migration enables product presets that can be reused across multiple campaigns,
-- eliminating the need to re-upload product photos and re-extract product profiles
-- every time a new campaign is created.

-- Add archived field for soft deletion
ALTER TABLE products
ADD COLUMN archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Add index for faster product lookups by user and brand
CREATE INDEX IF NOT EXISTS idx_products_user_id_created
ON products(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_products_brand_id
ON products(brand_id);

-- Add comments explaining fields
COMMENT ON COLUMN products.archived IS
'Soft delete flag - archived products are hidden from library but preserved for existing campaigns';

COMMENT ON COLUMN products.description_text IS
'Supplementary description of the product (optional, product photos are primary reference)';
