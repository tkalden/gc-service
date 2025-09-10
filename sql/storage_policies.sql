-- Supabase Storage RLS Policies Fix
-- Run this SQL in your Supabase Dashboard > SQL Editor

-- Enable RLS on storage.objects table
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Authenticated users can upload images" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can view images" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can update images" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated users can delete images" ON storage.objects;
DROP POLICY IF EXISTS "Public can view images" ON storage.objects;

-- Create policy for authenticated users to upload images to their own folder
CREATE POLICY "Authenticated users can upload images" ON storage.objects
FOR INSERT WITH CHECK (
    auth.role() = 'authenticated' 
    AND bucket_id = 'clothing-images'
    AND (storage.foldername(name))[1] = 'user-clothes'
    AND (storage.foldername(name))[2] = auth.uid()::text
);

-- Create policy for authenticated users to view their own images
CREATE POLICY "Authenticated users can view images" ON storage.objects
FOR SELECT USING (
    auth.role() = 'authenticated' 
    AND bucket_id = 'clothing-images'
    AND (storage.foldername(name))[1] = 'user-clothes'
    AND (storage.foldername(name))[2] = auth.uid()::text
);

-- Create policy for authenticated users to update their own images
CREATE POLICY "Authenticated users can update images" ON storage.objects
FOR UPDATE USING (
    auth.role() = 'authenticated' 
    AND bucket_id = 'clothing-images'
    AND (storage.foldername(name))[1] = 'user-clothes'
    AND (storage.foldername(name))[2] = auth.uid()::text
);

-- Create policy for authenticated users to delete their own images
CREATE POLICY "Authenticated users can delete images" ON storage.objects
FOR DELETE USING (
    auth.role() = 'authenticated' 
    AND bucket_id = 'clothing-images'
    AND (storage.foldername(name))[1] = 'user-clothes'
    AND (storage.foldername(name))[2] = auth.uid()::text
);

-- Optional: Allow public read access to images
-- Remove this policy if you want images to be private
CREATE POLICY "Public can view images" ON storage.objects
FOR SELECT USING (
    bucket_id = 'clothing-images'
);

-- Verify policies were created
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'objects' AND schemaname = 'storage';
