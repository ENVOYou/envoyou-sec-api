-- Migration to add missing auth columns to users table
-- Run this in Supabase SQL Editor

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS auth_provider_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Asia/Jakarta',
ADD COLUMN IF NOT EXISTS avatar_url TEXT,
ADD COLUMN IF NOT EXISTS two_factor_secret VARCHAR(255),
ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;

-- Add unique constraint on auth_provider + auth_provider_id if needed
-- ALTER TABLE users ADD CONSTRAINT unique_auth_provider_id UNIQUE (auth_provider, auth_provider_id);
