-- Migration: Add extended metrics columns to post_metrics table
-- These columns store the enhanced metrics from Instagram/Facebook Insights APIs

ALTER TABLE post_metrics
  -- Extended engagement metrics (from Insights APIs)
  ADD COLUMN IF NOT EXISTS reach INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS saves INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS profile_visits INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS reposts INTEGER DEFAULT 0,

  -- Interaction metrics
  ADD COLUMN IF NOT EXISTS post_clicks INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS impressions INTEGER DEFAULT 0,

  -- Video-specific metrics
  ADD COLUMN IF NOT EXISTS avg_watch_time_seconds DECIMAL(10,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS total_watch_time_seconds BIGINT DEFAULT 0,

  -- Promotional/conversion metrics (aggregated from conversions table)
  ADD COLUMN IF NOT EXISTS link_clicks INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS add_to_cart_count INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS conversion_count INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS conversion_value DECIMAL(10,2) DEFAULT 0;

-- Indexes for querying high-performing posts
CREATE INDEX IF NOT EXISTS idx_post_metrics_reach ON post_metrics(reach);
CREATE INDEX IF NOT EXISTS idx_post_metrics_saves ON post_metrics(saves);
CREATE INDEX IF NOT EXISTS idx_post_metrics_conversions ON post_metrics(conversion_count);
CREATE INDEX IF NOT EXISTS idx_post_metrics_watch_time ON post_metrics(avg_watch_time_seconds);

-- Comments
COMMENT ON COLUMN post_metrics.reach IS 'Unique users who saw this post (Instagram/Facebook Insights)';
COMMENT ON COLUMN post_metrics.saves IS 'Number of times post was saved (Instagram Insights)';
COMMENT ON COLUMN post_metrics.profile_visits IS 'Profile visits attributed to this post (Instagram Insights)';
COMMENT ON COLUMN post_metrics.reposts IS 'Number of times post was shared to stories (Instagram Insights)';
COMMENT ON COLUMN post_metrics.post_clicks IS 'Total clicks on the post (Facebook Page Insights)';
COMMENT ON COLUMN post_metrics.impressions IS 'Total times post was shown (Facebook/Instagram Insights)';
COMMENT ON COLUMN post_metrics.avg_watch_time_seconds IS 'Average watch time for video content (Instagram Reels)';
COMMENT ON COLUMN post_metrics.total_watch_time_seconds IS 'Total watch time across all views (Instagram Reels)';
COMMENT ON COLUMN post_metrics.link_clicks IS 'Clicks on UTM-tagged links in the post';
COMMENT ON COLUMN post_metrics.add_to_cart_count IS 'Number of add-to-cart events attributed to this post';
COMMENT ON COLUMN post_metrics.conversion_count IS 'Number of purchases attributed to this post';
COMMENT ON COLUMN post_metrics.conversion_value IS 'Total revenue generated from this post';
