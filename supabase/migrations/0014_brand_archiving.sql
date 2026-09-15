-- Add archiving functionality for brands instead of hard delete
-- This allows brands to be removed from library while keeping campaign references intact

-- Add archived flag to brands table
ALTER TABLE brands
ADD COLUMN archived BOOLEAN NOT NULL DEFAULT FALSE;

-- Add index for filtering archived brands
CREATE INDEX idx_brands_archived
ON brands(user_id, archived, created_at DESC);

-- Update the existing index to include archived status
DROP INDEX IF EXISTS idx_brands_user_id_created;
CREATE INDEX idx_brands_user_id_created
ON brands(user_id, created_at DESC) WHERE archived = FALSE;
