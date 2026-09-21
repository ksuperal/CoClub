-- Migration: Add conversion tracking for e-commerce events
-- Tracks ViewContent, AddToCart, and Purchase events from Meta Pixel

CREATE TABLE conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    post_id UUID REFERENCES posts(id) ON DELETE SET NULL,
    variant_id UUID REFERENCES variants(id) ON DELETE SET NULL,

    -- Event details
    event_type TEXT NOT NULL CHECK (event_type IN ('ViewContent', 'AddToCart', 'Purchase', 'InitiateCheckout')),
    event_time TIMESTAMPTZ NOT NULL,

    -- Product/Order details
    content_ids TEXT[] DEFAULT ARRAY[]::TEXT[],
    content_type TEXT DEFAULT 'product',
    value DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    num_items INTEGER,

    -- Attribution (from UTM parameters)
    utm_source TEXT,
    utm_campaign TEXT,

    -- External tracking
    external_id TEXT,  -- From Meta Pixel event_id for deduplication

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for query performance
CREATE INDEX idx_conversions_campaign ON conversions(campaign_id);
CREATE INDEX idx_conversions_post ON conversions(post_id);
CREATE INDEX idx_conversions_variant ON conversions(variant_id);
CREATE INDEX idx_conversions_event_type ON conversions(event_type);
CREATE INDEX idx_conversions_event_time ON conversions(event_time);
CREATE INDEX idx_conversions_utm_campaign ON conversions(utm_campaign);

-- Row-level security
ALTER TABLE conversions ENABLE ROW LEVEL SECURITY;

-- Users can only see conversions for their own campaigns
CREATE POLICY conversions_select ON conversions
  FOR SELECT
  USING (
    campaign_id IN (
      SELECT id FROM campaigns WHERE user_id = auth.uid()
    )
  );

-- Comments
COMMENT ON TABLE conversions IS 'Tracks conversion events (view, add-to-cart, purchase) from social posts';
COMMENT ON COLUMN conversions.event_type IS 'Type of conversion event';
COMMENT ON COLUMN conversions.value IS 'Monetary value of the conversion';
COMMENT ON COLUMN conversions.external_id IS 'Meta Pixel event_id for deduplication';
