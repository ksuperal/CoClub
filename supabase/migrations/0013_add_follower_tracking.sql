-- Migration: Add follower tracking to social_accounts
-- This allows tracking follower growth over time for branding content metrics

ALTER TABLE social_accounts
  ADD COLUMN IF NOT EXISTS follower_count INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS follower_count_updated_at TIMESTAMPTZ;

-- Index for performance when querying recent follower counts
CREATE INDEX IF NOT EXISTS idx_social_accounts_follower_updated
  ON social_accounts(follower_count_updated_at);

-- Add comment
COMMENT ON COLUMN social_accounts.follower_count IS 'Current follower/fan count for this account';
COMMENT ON COLUMN social_accounts.follower_count_updated_at IS 'When the follower count was last refreshed';
