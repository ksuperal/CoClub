-- Make product-assets bucket public so product images can be displayed
-- This allows public URL access to uploaded product photos in the product library

UPDATE storage.buckets
SET public = true
WHERE id = 'product-assets';
