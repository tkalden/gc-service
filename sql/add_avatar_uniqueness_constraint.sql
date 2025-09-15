-- Migration: Add Unique Constraint for One Avatar Per User
-- Description: Ensures each user can only have one avatar by adding a unique constraint

-- First, remove any duplicate avatars (keep the latest one for each user)
WITH latest_avatars AS (
    SELECT DISTINCT ON (user_id) id, user_id
    FROM avatars
    ORDER BY user_id, created_at DESC
)
DELETE FROM avatars 
WHERE id NOT IN (SELECT id FROM latest_avatars);

-- Add unique constraint on user_id to ensure one avatar per user
ALTER TABLE avatars 
ADD CONSTRAINT unique_user_avatar UNIQUE (user_id);

-- Add comment for documentation
COMMENT ON CONSTRAINT unique_user_avatar ON avatars IS 'Ensures each user can only have one avatar';
