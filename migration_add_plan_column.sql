-- Migration: Add plan column to users table
-- Run this to add plan support to existing database

ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'FREE';

-- Optional: Update existing users with specific plans based on email domain
-- UPDATE users SET plan = 'ENTERPRISE' WHERE email LIKE '%@envoyou.com';