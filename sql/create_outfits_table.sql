-- Migration: Create Outfits Table
-- Description: Creates table for storing user outfits with multiple images and metadata

-- Create outfits table
CREATE TABLE IF NOT EXISTS outfits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL DEFAULT 'My Outfit',
    description TEXT,
    image_urls JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of image URLs
    clothing_item_ids JSONB DEFAULT '[]'::jsonb, -- Array of clothing item IDs used in outfit
    outfit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    season VARCHAR(20) CHECK (season IN ('spring', 'summer', 'fall', 'winter', 'all-season')),
    occasion VARCHAR(50), -- e.g., 'casual', 'formal', 'work', 'party', 'sports'
    weather_condition VARCHAR(50), -- e.g., 'sunny', 'rainy', 'cold', 'hot'
    rating INTEGER CHECK (rating >= 1 AND rating <= 5), -- User rating 1-5 stars
    is_favorite BOOLEAN DEFAULT FALSE,
    tags JSONB DEFAULT '[]'::jsonb, -- Array of tags for search/filtering
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_outfits_user_id ON outfits(user_id);
CREATE INDEX IF NOT EXISTS idx_outfits_outfit_date ON outfits(outfit_date DESC);
CREATE INDEX IF NOT EXISTS idx_outfits_created_at ON outfits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_outfits_season ON outfits(season);
CREATE INDEX IF NOT EXISTS idx_outfits_occasion ON outfits(occasion);
CREATE INDEX IF NOT EXISTS idx_outfits_is_favorite ON outfits(is_favorite);

-- Create GIN index for JSONB columns for efficient querying
CREATE INDEX IF NOT EXISTS idx_outfits_image_urls_gin ON outfits USING GIN (image_urls);
CREATE INDEX IF NOT EXISTS idx_outfits_clothing_item_ids_gin ON outfits USING GIN (clothing_item_ids);
CREATE INDEX IF NOT EXISTS idx_outfits_tags_gin ON outfits USING GIN (tags);

-- Enable Row Level Security (RLS)
ALTER TABLE outfits ENABLE ROW LEVEL SECURITY;

-- RLS Policies for outfits table
-- Users can only see their own outfits
CREATE POLICY "Users can view their own outfits" 
    ON outfits FOR SELECT 
    USING (auth.uid() = user_id);

-- Users can insert their own outfits
CREATE POLICY "Users can insert their own outfits" 
    ON outfits FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own outfits
CREATE POLICY "Users can update their own outfits" 
    ON outfits FOR UPDATE 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own outfits
CREATE POLICY "Users can delete their own outfits" 
    ON outfits FOR DELETE 
    USING (auth.uid() = user_id);

-- Create updated_at trigger for outfits table
CREATE TRIGGER update_outfits_updated_at 
    BEFORE UPDATE ON outfits 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL ON outfits TO authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Add comments for documentation
COMMENT ON TABLE outfits IS 'Stores user outfits with multiple images and metadata';
COMMENT ON COLUMN outfits.image_urls IS 'JSONB array of image URLs for the outfit';
COMMENT ON COLUMN outfits.clothing_item_ids IS 'JSONB array of clothing item IDs used in this outfit';
COMMENT ON COLUMN outfits.outfit_date IS 'Date when the outfit was worn/created';
COMMENT ON COLUMN outfits.season IS 'Season for which this outfit is suitable';
COMMENT ON COLUMN outfits.occasion IS 'Occasion or event type for this outfit';
COMMENT ON COLUMN outfits.weather_condition IS 'Weather condition this outfit is suitable for';
COMMENT ON COLUMN outfits.rating IS 'User rating from 1 to 5 stars';
COMMENT ON COLUMN outfits.tags IS 'JSONB array of tags for search and filtering';
