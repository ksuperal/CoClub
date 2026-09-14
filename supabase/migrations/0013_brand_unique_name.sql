-- Ensure brand names are unique per user (case-insensitive)
-- This prevents duplicate brand creation and ensures data integrity

-- First, remove any duplicate brands (keeping only the most recent one per name)
-- This query identifies duplicates and keeps only the latest created brand
DELETE FROM brands
WHERE id IN (
  SELECT b1.id
  FROM brands b1
  INNER JOIN brands b2
    ON b1.user_id = b2.user_id
    AND LOWER(b1.name) = LOWER(b2.name)
    AND b1.created_at < b2.created_at
);

-- Create a unique index on (user_id, LOWER(name)) to enforce case-insensitive uniqueness
-- This ensures each user can only have one brand with a given name (ignoring case)
CREATE UNIQUE INDEX idx_brands_user_name_unique
ON brands (user_id, LOWER(name));
