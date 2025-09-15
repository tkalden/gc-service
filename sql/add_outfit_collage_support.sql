-- Migration: Add collage support to outfits table
-- This adds support for custom positioning of clothing items in outfits

-- Add new columns to outfits table
ALTER TABLE outfits 
ADD COLUMN IF NOT EXISTS is_collage BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS canvas_layout JSONB DEFAULT '{}';

-- Add comments for documentation
COMMENT ON COLUMN outfits.is_collage IS 'Whether this outfit has custom positioning (collage mode)';
COMMENT ON COLUMN outfits.canvas_layout IS 'JSON object storing custom positions and sizes for each clothing item category';

-- Create index on is_collage for better query performance
CREATE INDEX IF NOT EXISTS idx_outfits_is_collage ON outfits(is_collage);

-- Example of canvas_layout structure:
-- {
--   "tops": {
--     "position": {"x": 80, "y": 40},
--     "size": 100
--   },
--   "bottoms": {
--     "position": {"x": 50, "y": 120},
--     "size": 140
--   },
--   "shoes": {
--     "position": {"x": 20, "y": 280},
--     "size": 90
--   }
-- }
