-- Add follower_growth column to campaign_reports to store platform-specific follower growth during campaign

ALTER TABLE campaign_reports
  ADD COLUMN IF NOT EXISTS follower_growth JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN campaign_reports.follower_growth IS 'Platform-specific follower growth during campaign period, e.g., {"instagram": 45, "facebook": 12, "tiktok": 103}';
