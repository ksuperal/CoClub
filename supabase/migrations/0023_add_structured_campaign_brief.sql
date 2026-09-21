-- Add structured campaign brief fields
-- This replaces the simple "brief text" with a comprehensive structured brief
-- that helps Claude generate better, more targeted campaigns

-- Add structured brief as JSONB for flexibility
ALTER TABLE campaigns
  ADD COLUMN IF NOT EXISTS structured_brief JSONB DEFAULT '{}'::jsonb;

-- Add index for better query performance on structured brief
CREATE INDEX IF NOT EXISTS idx_campaigns_structured_brief
  ON campaigns USING GIN (structured_brief);

-- Comment explaining the structure
COMMENT ON COLUMN campaigns.structured_brief IS
'Structured campaign brief with the following fields:
{
  "objective": "What the content should achieve",
  "target_audience": "Who we want to attract/reach",
  "single_minded_message": "The one message we want audience to remember",
  "usp": "Unique selling proposition - key selling point and reason",
  "reason_to_believe": "Evidence or development proof that builds credibility",
  "cta": "Call to action - what we want audience to do (e.g., buy now, download app)",
  "mandatory_information": "Required elements (e.g., price, promotion dates, logo)",
  "reference": "Mood & Tone reference/examples",
  "format": "Content format (e.g., 1:1, 4:5, 9:16)"
}

Note: The old "brief" text field is kept for backwards compatibility but should
be populated from structured_brief going forward.';

-- Create a function to sync brief text from structured_brief for display
CREATE OR REPLACE FUNCTION sync_brief_from_structured()
RETURNS TRIGGER AS $$
BEGIN
  -- Auto-generate a summary brief text from structured fields if structured_brief is populated
  IF NEW.structured_brief IS NOT NULL AND NEW.structured_brief::text != '{}'::text THEN
    NEW.brief := COALESCE(
      'Objective: ' || (NEW.structured_brief->>'objective') || E'\n' ||
      'Target Audience: ' || (NEW.structured_brief->>'target_audience') || E'\n' ||
      'Message: ' || (NEW.structured_brief->>'single_minded_message'),
      NEW.brief
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-sync brief text when structured_brief is updated
DROP TRIGGER IF EXISTS trigger_sync_brief_from_structured ON campaigns;
CREATE TRIGGER trigger_sync_brief_from_structured
  BEFORE INSERT OR UPDATE OF structured_brief ON campaigns
  FOR EACH ROW
  EXECUTE FUNCTION sync_brief_from_structured();
