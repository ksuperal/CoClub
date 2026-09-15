-- Make brand-assets bucket public so moodboard images can be displayed
-- This allows public URL access to uploaded moodboard and brand guideline files

UPDATE storage.buckets
SET public = true
WHERE id = 'brand-assets';
