#!/usr/bin/env python3
"""
Migrate data from SQLite (app.db) to Supabase Postgres
"""

import os
import sqlite3
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.api_key import APIKey
from app.models.session import Session
from app.models.notification import NotificationTemplate

# Load environment variables
load_dotenv()

# Database URLs
SQLITE_DB = "app.db"
SUPABASE_URL = os.getenv("DATABASE_URL")

def get_sqlite_data(table_name):
    """Get all data from SQLite table as dict"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def migrate_users(supabase_session, data):
    """Migrate users data"""
    for row in data:
        # Skip if user already exists
        existing = supabase_session.query(User).filter_by(id=row['id']).first()
        if existing:
            continue

        user = User(
            id=row['id'],
            email=row['email'],
            password_hash=row['password_hash'],
            name=row['name'],
            company=row['company'],
            job_title=row['job_title'],
            avatar_url=row['avatar_url'],
            timezone=row['timezone'],
            email_verified=row['email_verified'],
            email_verification_token=row['email_verification_token'],
            email_verification_expires=row['email_verification_expires'],
            password_reset_token=row['password_reset_token'],
            password_reset_expires=row['password_reset_expires'],
            last_login=row['last_login'],
            two_factor_secret=row['two_factor_secret'],
            two_factor_enabled=row['two_factor_enabled'],
            auth_provider=row['auth_provider'],
            auth_provider_id=row['auth_provider_id'],
            plan=row.get('plan', 'FREE'),
            paddle_customer_id=row.get('paddle_customer_id'),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        supabase_session.add(user)

def migrate_api_keys(supabase_session, data):
    """Migrate API keys data"""
    for row in data:
        # Check if user exists
        user_exists = supabase_session.query(User).filter_by(id=row['user_id']).first()
        if not user_exists:
            print(f"Skipping API key for non-existent user {row['user_id']}")
            continue

        # Skip if key already exists
        existing = supabase_session.query(APIKey).filter_by(id=row['id']).first()
        if existing:
            continue

        api_key = APIKey(
            user_id=row['user_id'],
            name=row['name']
        )
        # Set the other fields manually
        api_key.id = row['id']
        api_key.key_hash = row['key_hash']
        api_key.prefix = row['prefix']
        api_key.permissions = row['permissions']
        api_key.is_active = row['is_active']
        api_key.last_used = row['last_used']
        api_key.usage_count = row['usage_count']
        api_key.created_at = row['created_at']
        api_key.updated_at = row['updated_at']
        supabase_session.add(api_key)

def migrate_sessions(supabase_session, data):
    """Migrate sessions data"""
    for row in data:
        # Check if user exists
        user_exists = supabase_session.query(User).filter_by(id=row['user_id']).first()
        if not user_exists:
            print(f"Skipping session for non-existent user {row['user_id']}")
            continue

        # Skip if session already exists
        existing = supabase_session.query(Session).filter_by(id=row['id']).first()
        if existing:
            continue

        session_obj = Session(
            user_id=row['user_id'],
            token="dummy"  # Will be overridden
        )
        # Set the other fields manually
        session_obj.id = row['id']
        session_obj.token_hash = row['token_hash']
        session_obj.device_info = row['device_info']
        session_obj.ip_address = row['ip_address']
        session_obj.location = row['location']
        session_obj.expires_at = row['expires_at']
        session_obj.created_at = row['created_at']
        session_obj.last_active = row['last_active']
        supabase_session.add(session_obj)

def migrate_notification_templates(supabase_session, data):
    """Migrate notification templates data"""
    for row in data:
        # Skip if template already exists
        existing = supabase_session.query(NotificationTemplate).filter_by(key=row['key']).first()
        if existing:
            continue

        template = NotificationTemplate(
            id=row['id'],
            key=row['key'],
            name=row['name'],
            description=row['description'],
            type=row['type'],
            category=row['category'],
            priority=row['priority'],
            subject_template=row['subject_template'],
            message_template=row['message_template'],
            html_template=row['html_template'],
            data_fields=row['data_fields'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
        supabase_session.add(template)

def main():
    """Main migration function"""
    print("Starting data migration from SQLite to Supabase...")

    # Connect to Supabase
    supabase_engine = create_engine(SUPABASE_URL, echo=False)
    SupabaseSession = sessionmaker(bind=supabase_engine)
    supabase_session = SupabaseSession()

    try:
        # Migrate users
        users_data = get_sqlite_data('users')
        print(f"Found {len(users_data)} users")
        migrate_users(supabase_session, users_data)
        supabase_session.commit()
        print("Users migrated")

        # Migrate API keys
        api_keys_data = get_sqlite_data('api_keys')
        print(f"Found {len(api_keys_data)} API keys")
        migrate_api_keys(supabase_session, api_keys_data)
        supabase_session.commit()
        print("API keys migrated")

        # Migrate sessions
        sessions_data = get_sqlite_data('sessions')
        print(f"Found {len(sessions_data)} sessions")
        migrate_sessions(supabase_session, sessions_data)
        supabase_session.commit()
        print("Sessions migrated")

        # Migrate notification templates
        templates_data = get_sqlite_data('notification_templates')
        print(f"Found {len(templates_data)} notification templates")
        migrate_notification_templates(supabase_session, templates_data)
        supabase_session.commit()
        print("Notification templates migrated")

        print("Migration completed successfully!")

    except Exception as e:
        supabase_session.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        supabase_session.close()

if __name__ == "__main__":
    main()