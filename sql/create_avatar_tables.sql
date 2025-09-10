-- Migration: Create Digital Twin Avatar Tables
-- Description: Creates tables for storing user avatars and virtual try-on results

-- Create avatars table
CREATE TABLE IF NOT EXISTS avatars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    original_image_path TEXT NOT NULL,
    processed_image_path TEXT,
    pose_keypoints JSONB,
    body_segments JSONB,
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_avatars_user_id ON avatars(user_id);
CREATE INDEX IF NOT EXISTS idx_avatars_created_at ON avatars(created_at DESC);

-- Create try-on results table
CREATE TABLE IF NOT EXISTS tryon_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    avatar_id UUID NOT NULL REFERENCES avatars(id) ON DELETE CASCADE,
    clothing_item_id UUID NOT NULL REFERENCES clothing_items(id) ON DELETE CASCADE,
    result_image_path TEXT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    processing_time DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for try-on results
CREATE INDEX IF NOT EXISTS idx_tryon_results_user_id ON tryon_results(user_id);
CREATE INDEX IF NOT EXISTS idx_tryon_results_avatar_id ON tryon_results(avatar_id);
CREATE INDEX IF NOT EXISTS idx_tryon_results_created_at ON tryon_results(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE avatars ENABLE ROW LEVEL SECURITY;
ALTER TABLE tryon_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies for avatars table
-- Users can only see their own avatars
CREATE POLICY "Users can view their own avatars" 
    ON avatars FOR SELECT 
    USING (auth.uid() = user_id);

-- Users can insert their own avatars
CREATE POLICY "Users can insert their own avatars" 
    ON avatars FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own avatars
CREATE POLICY "Users can update their own avatars" 
    ON avatars FOR UPDATE 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own avatars
CREATE POLICY "Users can delete their own avatars" 
    ON avatars FOR DELETE 
    USING (auth.uid() = user_id);

-- RLS Policies for tryon_results table
-- Users can only see their own try-on results
CREATE POLICY "Users can view their own try-on results" 
    ON tryon_results FOR SELECT 
    USING (auth.uid() = user_id);

-- Users can insert their own try-on results
CREATE POLICY "Users can insert their own try-on results" 
    ON tryon_results FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own try-on results
CREATE POLICY "Users can delete their own try-on results" 
    ON tryon_results FOR DELETE 
    USING (auth.uid() = user_id);

-- Create updated_at trigger for avatars table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_avatars_updated_at 
    BEFORE UPDATE ON avatars 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL ON avatars TO authenticated;
GRANT ALL ON tryon_results TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Create storage bucket for digital twins if it doesn't exist
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'digital-twin',
    'digital-twin',
    false,
    10485760, -- 10MB limit
    ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for digital-twin bucket
-- Users can upload to their own folder
CREATE POLICY "Users can upload their own avatars"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'digital-twin' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can view their own avatars
CREATE POLICY "Users can view their own avatars"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'digital-twin' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can update their own avatars
CREATE POLICY "Users can update their own avatars"
    ON storage.objects FOR UPDATE
    USING (
        bucket_id = 'digital-twin' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Users can delete their own avatars
CREATE POLICY "Users can delete their own avatars"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'digital-twin' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Add comments for documentation
COMMENT ON TABLE avatars IS 'Stores user digital twin avatars with pose and segmentation data';
COMMENT ON TABLE tryon_results IS 'Stores virtual try-on results and metadata';

COMMENT ON COLUMN avatars.pose_keypoints IS 'MediaPipe pose detection keypoints in JSON format';
COMMENT ON COLUMN avatars.body_segments IS 'Body segmentation data from MediaPipe';
COMMENT ON COLUMN avatars.confidence_score IS 'Avatar quality score from 0.0 to 1.0';

COMMENT ON COLUMN tryon_results.confidence_score IS 'Try-on quality confidence from 0.0 to 1.0';
COMMENT ON COLUMN tryon_results.processing_time IS 'Time taken to process try-on in seconds';
