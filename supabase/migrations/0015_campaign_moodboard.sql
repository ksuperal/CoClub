-- Add moodboard support for campaigns
-- Allows users to upload visual references during campaign scoping

-- Add moodboard_assets column to campaigns table
ALTER TABLE campaigns
ADD COLUMN moodboard_assets TEXT[] DEFAULT '{}';

COMMENT ON COLUMN campaigns.moodboard_assets IS 'Array of Supabase storage paths for moodboard/reference images uploaded during scoping';
