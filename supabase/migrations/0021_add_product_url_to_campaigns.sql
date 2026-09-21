-- Add product_url field to campaigns for UTM link generation

ALTER TABLE campaigns
  ADD COLUMN IF NOT EXISTS product_url TEXT;

COMMENT ON COLUMN campaigns.product_url IS 'Optional product/landing page URL that will be added to post captions with UTM tracking. Example: https://yourstore.com/product/nike-shoes';
