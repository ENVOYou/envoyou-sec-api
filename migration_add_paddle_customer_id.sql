-- Migration: Add paddle_customer_id column to users table
-- Run this to add Paddle payment support to existing database

ALTER TABLE users ADD COLUMN paddle_customer_id TEXT;