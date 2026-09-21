-- Migration: Add link click tracking for UTM-tagged URLs
-- This enables tracking which social posts drive traffic to the website

CREATE TABLE link_clicks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE SET NULL,
    variant_id UUID REFERENCES variants(id) ON DELETE SET NULL,

    -- UTM parameters from the clicked link
    utm_source TEXT NOT NULL,  -- 'instagram', 'facebook', 'tiktok'
    utm_medium TEXT DEFAULT 'social',
    utm_campaign TEXT NOT NULL,  -- campaign_id
    utm_content TEXT,  -- variant_id or post_id

    -- Click data
    clicked_url TEXT NOT NULL,
    destination_url TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT,
    referrer TEXT,

    -- Metadata
    clicked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX idx_link_clicks_campaign ON link_clicks(campaign_id);
CREATE INDEX idx_link_clicks_post ON link_clicks(post_id);
CREATE INDEX idx_link_clicks_variant ON link_clicks(variant_id);
CREATE INDEX idx_link_clicks_clicked_at ON link_clicks(clicked_at);
CREATE INDEX idx_link_clicks_utm_source ON link_clicks(utm_source);

-- Row-level security
ALTER TABLE link_clicks ENABLE ROW LEVEL SECURITY;

-- Users can only see clicks for their own campaigns
CREATE POLICY link_clicks_select ON link_clicks
  FOR SELECT
  USING (
    campaign_id IN (
      SELECT id FROM campaigns WHERE user_id = auth.uid()
    )
  );

-- Comments
COMMENT ON TABLE link_clicks IS 'Tracks clicks on UTM-tagged links from social media posts';
COMMENT ON COLUMN link_clicks.utm_source IS 'Social platform where the click originated';
COMMENT ON COLUMN link_clicks.clicked_at IS 'When the user clicked the link';
