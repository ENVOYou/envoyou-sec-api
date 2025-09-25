#!/usr/bin/env python3
"""
Staging Migration Script for Envoyou SEC API
Safely migrates database schema to Supabase staging environment.
"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run shell command with logging."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(f"STDOUT: {result.stdout}")
    if result.stderr:
        print(f"STDERR: {result.stderr}")
    
    if check and result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(1)
    
    return result

def check_environment():
    """Check required environment variables."""
    required_vars = ["DATABASE_URL"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"Missing required environment variables: {missing}")
        sys.exit(1)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url.startswith("postgresql://"):
        print("DATABASE_URL must be a PostgreSQL connection string")
        sys.exit(1)
    
    print("✓ Environment variables validated")

def backup_database():
    """Create database backup before migration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"staging_backup_{timestamp}.sql"
    
    db_url = os.getenv("DATABASE_URL")
    
    print(f"Creating backup: {backup_file}")
    run_command(f"pg_dump '{db_url}' > {backup_file}")
    
    print(f"✓ Backup created: {backup_file}")
    return backup_file

def preview_migration():
    """Preview migration SQL without applying."""
    print("Previewing migration SQL...")
    
    preview_file = f"migration_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    run_command(f"alembic upgrade --sql head > {preview_file}")
    
    print(f"✓ Migration preview saved: {preview_file}")
    
    # Show first 50 lines
    with open(preview_file, 'r') as f:
        lines = f.readlines()[:50]
        print("\nFirst 50 lines of migration:")
        print("=" * 50)
        print(''.join(lines))
        if len(lines) == 50:
            print("... (truncated)")
        print("=" * 50)
    
    return preview_file

def apply_migration():
    """Apply Alembic migration."""
    print("Applying migration...")
    run_command("alembic upgrade head")
    print("✓ Migration applied successfully")

def seed_data():
    """Seed minimal data for staging."""
    print("Seeding minimal data...")
    
    # Create seed script
    seed_script = """
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.repositories.company_map_repository import upsert_mapping

# Connect to database
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Seed demo mapping
    upsert_mapping(
        db,
        company="Demo Company",
        facility_id="12345",
        facility_name="Demo Facility",
        state="TX",
        notes="Demo mapping for staging"
    )
    
    print("✓ Demo mapping created")
    
except Exception as e:
    print(f"Error seeding data: {e}")
    db.rollback()
finally:
    db.close()
"""
    
    with open("temp_seed.py", "w") as f:
        f.write(seed_script)
    
    try:
        run_command("python3 temp_seed.py")
        print("✓ Minimal data seeded")
    finally:
        os.remove("temp_seed.py")

def smoke_test():
    """Run basic smoke tests."""
    print("Running smoke tests...")
    
    # Test database connection
    test_script = """
import os
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
    print(f"Alembic version table has {result.scalar()} rows")
    
    result = conn.execute(text("SELECT COUNT(*) FROM company_facility_map"))
    print(f"Company mapping table has {result.scalar()} rows")

print("✓ Database connection and tables verified")
"""
    
    with open("temp_smoke.py", "w") as f:
        f.write(test_script)
    
    try:
        run_command("python3 temp_smoke.py")
        print("✓ Smoke tests passed")
    finally:
        os.remove("temp_smoke.py")

def main():
    """Main migration workflow."""
    print("=== Envoyou SEC API - Staging Migration ===")
    print(f"Started at: {datetime.now()}")
    
    # Pre-flight checks
    check_environment()
    
    # Backup
    backup_file = backup_database()
    
    # Preview
    preview_file = preview_migration()
    
    # Confirm
    response = input("\nProceed with migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled")
        sys.exit(0)
    
    try:
        # Apply migration
        apply_migration()
        
        # Seed data
        seed_data()
        
        # Smoke test
        smoke_test()
        
        print("\n✓ Staging migration completed successfully!")
        print(f"Backup: {backup_file}")
        print(f"Preview: {preview_file}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"Restore from backup: pg_restore {backup_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()