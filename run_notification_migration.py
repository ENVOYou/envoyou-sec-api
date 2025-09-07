#!/usr/bin/env python3
"""
Database Migration Script for Notification System
Run this script to create notification-related tables in the database
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    """Run the notification system database migration"""

    # Get database path
    db_path = os.getenv("DATABASE_URL", "app.db")
    if db_path.startswith("sqlite:///"):
        db_path = db_path.replace("sqlite:///", "")

    # Ensure database directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    print(f"📊 Running notification migration on database: {db_path}")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read migration file
        migration_file = Path(__file__).parent / "notification_migration.sql"
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False

        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # Execute migration
        cursor.executescript(migration_sql)
        conn.commit()

        print("✅ Notification migration completed successfully!")
        print("📋 Created tables:")
        print("   - notifications")
        print("   - notification_templates")
        print("   - notification_preferences")
        print("📋 Created indexes for performance optimization")
        print("📋 Inserted default notification templates")

        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'notification%';")
        tables = cursor.fetchall()
        print(f"📋 Verification: Found {len(tables)} notification tables")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
