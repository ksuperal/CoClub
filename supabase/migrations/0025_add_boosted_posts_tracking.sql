-- Migration: Add boosted posts and ad campaigns tracking
-- Enables tracking of promoted posts via Meta Ads API and TikTok Spark Ads

-- Store Meta/TikTok ad account information
CREATE TABLE IF NOT EXISTS ad_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Platform and account details
    platform TEXT NOT NULL CHECK (platform IN ('facebook', 'instagram', 'tiktok')),
    external_ad_account_id TEXT NOT NULL, -- act_123456789 for Meta, advertiser_id for TikTok
    external_ad_account_name TEXT,

    -- Business/brand association
    business_id TEXT, -- Meta Business Manager ID or TikTok Business Center ID
    currency TEXT DEFAULT 'USD',
    timezone TEXT,

    -- Account status
    account_status TEXT, -- ACTIVE, DISABLED, UNSETTLED, etc.

    -- Spend limits and balance
    spend_cap DECIMAL(10,2),
    amount_spent DECIMAL(10,2) DEFAULT 0,
    balance DECIMAL(10,2) DEFAULT 0,

    -- Metadata
    connected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, platform, external_ad_account_id)
);

-- Track individual boosted posts / ad campaigns
CREATE TABLE IF NOT EXISTS boosted_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Ownership and source
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,

    -- Platform info
    platform TEXT NOT NULL CHECK (platform IN ('facebook', 'instagram', 'tiktok')),

    -- External ad IDs from Meta/TikTok
    external_campaign_id TEXT, -- Meta Campaign ID or TikTok Campaign ID
    external_adset_id TEXT, -- Meta Ad Set ID or TikTok Ad Group ID
    external_ad_id TEXT, -- Meta Ad ID or TikTok Ad ID

    -- Boost configuration
    objective TEXT NOT NULL, -- REACH, ENGAGEMENT, LINK_CLICKS, CONVERSIONS, etc.
    optimization_goal TEXT, -- IMPRESSIONS, LINK_CLICKS, POST_ENGAGEMENT, etc.

    -- Budget and schedule
    budget_type TEXT NOT NULL CHECK (budget_type IN ('daily', 'lifetime')),
    budget_amount DECIMAL(10,2) NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,

    -- Targeting (stored as JSONB for flexibility)
    targeting JSONB DEFAULT '{}'::jsonb, -- {age_min, age_max, genders, locations, interests, etc.}

    -- Performance metrics (synced periodically)
    impressions BIGINT DEFAULT 0,
    reach INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    engagement INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    amount_spent DECIMAL(10,2) DEFAULT 0,

    -- Calculated metrics
    cpm DECIMAL(10,2) DEFAULT 0, -- Cost per 1000 impressions
    cpc DECIMAL(10,2) DEFAULT 0, -- Cost per click
    ctr DECIMAL(5,2) DEFAULT 0, -- Click-through rate

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'creating', 'active', 'paused', 'completed', 'failed', 'cancelled'
    )),
    error_message TEXT,

    -- AI recommendation context (why this post was suggested for boosting)
    boost_reason TEXT, -- "High organic engagement", "Exceeded expected saves by 200%", etc.
    ai_suggested BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_metrics_sync TIMESTAMPTZ
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ad_accounts_user ON ad_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_ad_accounts_platform ON ad_accounts(platform);

CREATE INDEX IF NOT EXISTS idx_boosted_posts_user ON boosted_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_boosted_posts_post ON boosted_posts(post_id);
CREATE INDEX IF NOT EXISTS idx_boosted_posts_campaign ON boosted_posts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_boosted_posts_status ON boosted_posts(status);
CREATE INDEX IF NOT EXISTS idx_boosted_posts_platform ON boosted_posts(platform);
CREATE INDEX IF NOT EXISTS idx_boosted_posts_ad_account ON boosted_posts(ad_account_id);

-- GIN index for targeting JSONB queries
CREATE INDEX IF NOT EXISTS idx_boosted_posts_targeting ON boosted_posts USING GIN (targeting);

-- Row Level Security
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE boosted_posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ad_accounts_owner_all" ON ad_accounts
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "boosted_posts_owner_all" ON boosted_posts
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Comments
COMMENT ON TABLE ad_accounts IS 'Stores connected Meta/TikTok ad accounts for programmatic post boosting';
COMMENT ON TABLE boosted_posts IS 'Tracks individual boosted posts and their ad campaign performance';

COMMENT ON COLUMN ad_accounts.external_ad_account_id IS 'Meta: act_123456789, TikTok: advertiser_id';
COMMENT ON COLUMN boosted_posts.targeting IS 'Audience targeting configuration: {age_min: 18, age_max: 65, genders: [1,2], locations: [{key: "US"}], interests: [...]}';
COMMENT ON COLUMN boosted_posts.ai_suggested IS 'Whether this boost was AI-recommended based on performance metrics';
COMMENT ON COLUMN boosted_posts.boost_reason IS 'AI explanation of why this post should be boosted';

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ad_accounts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ad_accounts_updated_at
    BEFORE UPDATE ON ad_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_ad_accounts_updated_at();

CREATE OR REPLACE FUNCTION update_boosted_posts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_boosted_posts_updated_at
    BEFORE UPDATE ON boosted_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_boosted_posts_updated_at();
