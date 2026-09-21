-- Create comprehensive content performance tracking system
-- This table aggregates post performance data with AI-generated improvement recommendations

CREATE TABLE IF NOT EXISTS content_performance_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Post identification
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Post details (denormalized for easy querying)
    platform TEXT NOT NULL, -- instagram, facebook, tiktok
    campaign_type TEXT NOT NULL, -- product_launch, brand_awareness, etc.
    content_type TEXT, -- educational, branding, promotional, review_demo
    message_angle TEXT,

    -- Performance metrics snapshot (latest)
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb, -- {likes, comments, shares, views, saves, reach, etc.}
    engagement_score INTEGER DEFAULT 0,

    -- Performance categorization
    performance_tier TEXT CHECK (performance_tier IN ('excellent', 'good', 'average', 'poor', 'needs_improvement')),
    performance_percentile DECIMAL(5,2), -- 0-100, relative to user's other posts

    -- Timing analysis
    posted_at TIMESTAMPTZ,
    best_posting_time_match BOOLEAN, -- Did this post at recommended time?
    day_of_week TEXT,
    hour_of_day INTEGER,

    -- Content analysis
    caption_length INTEGER,
    hashtag_count INTEGER,
    has_product_link BOOLEAN DEFAULT FALSE,
    media_type TEXT, -- image, video, carousel

    -- AI-generated insights and recommendations
    ai_analysis JSONB DEFAULT '{}'::jsonb, -- Structured analysis from AI
    improvement_recommendations TEXT[], -- Array of specific recommendations
    what_worked_well TEXT[], -- What performed well in this post
    what_needs_improvement TEXT[], -- What didn't work

    -- Comparative insights
    vs_user_average JSONB DEFAULT '{}'::jsonb, -- How this compares to user's average
    vs_platform_average JSONB DEFAULT '{}'::jsonb, -- How this compares to platform benchmarks
    similar_posts_reference UUID[], -- IDs of similar high-performing posts to learn from

    -- Status
    analysis_status TEXT DEFAULT 'pending' CHECK (analysis_status IN ('pending', 'analyzed', 'failed')),
    analyzed_at TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_performance_insights_post ON content_performance_insights(post_id);
CREATE INDEX idx_performance_insights_campaign ON content_performance_insights(campaign_id);
CREATE INDEX idx_performance_insights_user ON content_performance_insights(user_id);
CREATE INDEX idx_performance_insights_platform ON content_performance_insights(platform);
CREATE INDEX idx_performance_insights_performance_tier ON content_performance_insights(performance_tier);
CREATE INDEX idx_performance_insights_posted_at ON content_performance_insights(posted_at);
CREATE INDEX idx_performance_insights_content_type ON content_performance_insights(content_type);

-- GIN index for JSONB columns for fast querying
CREATE INDEX idx_performance_insights_metrics ON content_performance_insights USING GIN (metrics);
CREATE INDEX idx_performance_insights_ai_analysis ON content_performance_insights USING GIN (ai_analysis);

-- Row Level Security
ALTER TABLE content_performance_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "content_performance_insights_owner_all" ON content_performance_insights
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE content_performance_insights IS 'Comprehensive content performance tracking with AI-generated insights and improvement recommendations for past, ongoing, and future content optimization';
COMMENT ON COLUMN content_performance_insights.metrics IS 'Latest metrics snapshot: {likes, comments, shares, views, saves, reach, impressions, watch_time, profile_visits, follower_growth, etc.}';
COMMENT ON COLUMN content_performance_insights.ai_analysis IS 'Structured AI analysis: {strengths: [], weaknesses: [], opportunities: [], threats: [], recommended_changes: {}}';
COMMENT ON COLUMN content_performance_insights.performance_tier IS 'Performance category relative to user''s historical posts';
COMMENT ON COLUMN content_performance_insights.performance_percentile IS 'Percentile rank (0-100) compared to user''s other posts on same platform';
COMMENT ON COLUMN content_performance_insights.vs_user_average IS 'Comparison metrics: {engagement_rate_diff: +15%, reach_diff: -5%, etc.}';
COMMENT ON COLUMN content_performance_insights.similar_posts_reference IS 'Reference to similar high-performing posts user can learn from';

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_content_performance_insights_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_content_performance_insights_updated_at
    BEFORE UPDATE ON content_performance_insights
    FOR EACH ROW
    EXECUTE FUNCTION update_content_performance_insights_updated_at();
