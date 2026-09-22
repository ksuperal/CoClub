-- Migration: Add AI-driven campaign metrics and analysis
-- Enables automatic campaign type detection and success metric assignment

-- Add AI metrics to campaigns table
ALTER TABLE campaigns
  ADD COLUMN IF NOT EXISTS campaign_type TEXT,
  ADD COLUMN IF NOT EXISTS campaign_subtypes TEXT[] DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS primary_metric TEXT DEFAULT 'engagement_rate',
  ADD COLUMN IF NOT EXISTS secondary_metric TEXT,
  ADD COLUMN IF NOT EXISTS metrics_reasoning TEXT,
  ADD COLUMN IF NOT EXISTS expected_thresholds JSONB;

-- Add AI analysis to content_performance_insights table
ALTER TABLE content_performance_insights
  ADD COLUMN IF NOT EXISTS ai_analysis JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS what_worked_well TEXT[] DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS what_needs_improvement TEXT[] DEFAULT ARRAY[]::TEXT[],
  ADD COLUMN IF NOT EXISTS losing_stages JSONB DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS losing_points INTEGER DEFAULT 0;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_campaign_type ON campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_primary_metric ON campaigns(primary_metric);
CREATE INDEX IF NOT EXISTS idx_content_performance_losing_points ON content_performance_insights(losing_points);

-- Comments
COMMENT ON COLUMN campaigns.campaign_type IS
  'AI-detected campaign type (educational, promotional, brand_awareness, product_launch, etc.)';

COMMENT ON COLUMN campaigns.campaign_subtypes IS
  'Additional AI-detected characteristics (e.g., how-to-guide, product-comparison)';

COMMENT ON COLUMN campaigns.primary_metric IS
  'Primary success metric chosen by AI (saves, reach, link_clicks, conversions, etc.)';

COMMENT ON COLUMN campaigns.secondary_metric IS
  'Secondary success metric for additional insights';

COMMENT ON COLUMN campaigns.metrics_reasoning IS
  'AI explanation of why these metrics were chosen for this campaign';

COMMENT ON COLUMN campaigns.expected_thresholds IS
  'Expected performance levels: {excellent: {saves: 1000}, good: {saves: 800}, average: {saves: 500}}';

COMMENT ON COLUMN content_performance_insights.ai_analysis IS
  'AI-identified elements: {hook_type, visual_style, caption_strategy, format, why_it_worked}';

COMMENT ON COLUMN content_performance_insights.what_worked_well IS
  'Array of specific elements that drove success';

COMMENT ON COLUMN content_performance_insights.what_needs_improvement IS
  'Array of specific issues that caused underperformance';

COMMENT ON COLUMN content_performance_insights.losing_stages IS
  'Funnel stages where post failed: [{stage: "engagement", losing_points: 2, diagnosis: "..."}]';

COMMENT ON COLUMN content_performance_insights.losing_points IS
  'Total losing points (0-10 scale), higher = worse performance';
