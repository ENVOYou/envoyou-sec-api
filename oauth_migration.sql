-- OAuth Migration Script
-- Run this script to add OAuth support to existing databases

-- Add OAuth fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider_id TEXT;

-- Create index for faster OAuth lookups
CREATE INDEX IF NOT EXISTS idx_users_auth_provider ON users(auth_provider);
CREATE INDEX IF NOT EXISTS idx_users_auth_provider_id ON users(auth_provider_id);

-- Update comment
COMMENT ON COLUMN users.auth_provider IS 'OAuth provider: google, github, etc.';
COMMENT ON COLUMN users.auth_provider_id IS 'User ID from the OAuth provider';
