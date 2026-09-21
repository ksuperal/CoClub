-- Add follower_baseline column to campaigns to store starting follower counts when campaign posts

ALTER TABLE campaigns
  ADD COLUMN IF NOT EXISTS follower_baseline JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN campaigns.follower_baseline IS 'Baseline follower counts when campaign was posted, e.g., {"instagram": 100, "facebook": 50}. Used to calculate follower growth over the 24-hour campaign period.';
