-- Notification System Database Migration
-- Run this script to create notification-related tables

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'in_app',
    category VARCHAR(20) NOT NULL DEFAULT 'system',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    html_content TEXT,
    read BOOLEAN DEFAULT FALSE,
    read_at DATETIME,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create notification_templates table
CREATE TABLE IF NOT EXISTS notification_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(20) NOT NULL,
    category VARCHAR(20) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    subject_template VARCHAR(255),
    message_template TEXT NOT NULL,
    html_template TEXT,
    data_fields JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100) NOT NULL UNIQUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    email_verification BOOLEAN DEFAULT TRUE,
    email_security BOOLEAN DEFAULT TRUE,
    email_billing BOOLEAN DEFAULT TRUE,
    email_marketing BOOLEAN DEFAULT FALSE,
    email_system BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    in_app_account BOOLEAN DEFAULT TRUE,
    in_app_security BOOLEAN DEFAULT TRUE,
    in_app_billing BOOLEAN DEFAULT TRUE,
    in_app_system BOOLEAN DEFAULT TRUE,
    in_app_marketing BOOLEAN DEFAULT FALSE,
    push_enabled BOOLEAN DEFAULT TRUE,
    push_account BOOLEAN DEFAULT TRUE,
    push_security BOOLEAN DEFAULT TRUE,
    push_billing BOOLEAN DEFAULT TRUE,
    push_system BOOLEAN DEFAULT TRUE,
    push_marketing BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_category ON notifications(category);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notification_templates_key ON notification_templates(key);
CREATE INDEX IF NOT EXISTS idx_notification_templates_active ON notification_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);

-- Insert default notification templates
INSERT OR IGNORE INTO notification_templates (key, name, description, type, category, priority, subject_template, message_template, data_fields) VALUES
('welcome', 'Welcome Message', 'Welcome new users to the platform', 'email', 'account', 'high',
 'Welcome to Envoyou! 🎉',
 'Welcome to Envoyou! Your account has been created successfully. You can now access all our features and services.',
 '["user_name", "login_url"]'),

('email_verification', 'Email Verification', 'Verify user email addresses', 'email', 'security', 'urgent',
 'Verify Your Email - Envoyou',
 'Please verify your email address to complete your registration. Click the verification link to activate your account.',
 '["verification_url", "user_name"]'),

('password_reset', 'Password Reset', 'Reset user passwords', 'email', 'security', 'high',
 'Reset Your Password - Envoyou',
 'You requested a password reset. Click the link below to reset your password. This link will expire in 24 hours.',
 '["reset_url", "user_name"]'),

('password_changed', 'Password Changed', 'Notify when password is changed', 'email', 'security', 'medium',
 'Password Changed - Envoyou',
 'Your password has been successfully changed. If you did not make this change, please contact support immediately.',
 '["user_name", "change_time"]'),

('payment_success', 'Payment Success', 'Confirm successful payments', 'email', 'billing', 'medium',
 'Payment Successful - Envoyou',
 'Your payment has been processed successfully. Thank you for your business!',
 '["amount", "plan_name", "user_name"]'),

('payment_failed', 'Payment Failed', 'Alert failed payments', 'email', 'billing', 'urgent',
 'Payment Failed - Envoyou',
 'Your payment could not be processed. Please update your payment method to continue using our services.',
 '["amount", "failure_reason", "user_name"]'),

('subscription_expiring', 'Subscription Expiring', 'Warn about expiring subscriptions', 'email', 'billing', 'high',
 'Subscription Expiring Soon - Envoyou',
 'Your subscription will expire soon. Please renew to continue using our services without interruption.',
 '["expiry_date", "plan_name", "user_name"]'),

('login_alert', 'Login Alert', 'Alert users of new logins', 'email', 'security', 'medium',
 'New Login Detected - Envoyou',
 'We detected a new login to your account. If this was not you, please secure your account immediately.',
 '["login_time", "login_location", "device_info"]'),

('inactive_account', 'Inactive Account', 'Notify inactive users', 'email', 'security', 'medium',
 'Account Inactive - Envoyou',
 'We noticed you haven''t logged in for a while. Your account security is important to us.',
 '["last_login", "days_inactive", "user_name"]'),

('new_feature', 'New Feature', 'Announce new features', 'in_app', 'system', 'medium',
 'New Feature Available',
 'We''ve added a new feature to improve your experience. Check it out!',
 '["feature_name", "feature_description"]'),

('maintenance', 'Maintenance Notice', 'Notify about maintenance', 'in_app', 'system', 'medium',
 'Scheduled Maintenance',
 'We will be performing maintenance on our systems. Some services may be temporarily unavailable.',
 '["maintenance_time", "expected_downtime"]'),

('ticket_created', 'Support Ticket Created', 'Confirm support ticket creation', 'in_app', 'support', 'medium',
 'Support Ticket Created',
 'Your support ticket has been created and is being processed. We''ll get back to you soon.',
 '["ticket_id", "ticket_subject"]'),

('ticket_resolved', 'Support Ticket Resolved', 'Notify ticket resolution', 'in_app', 'support', 'medium',
 'Support Ticket Resolved',
 'Your support ticket has been resolved. Please check the resolution details.',
 '["ticket_id", "resolution_summary"]');

-- Insert default notification preferences for existing users (if users table exists)
-- This will be handled by the application when users are created
