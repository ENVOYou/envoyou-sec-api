#!/usr/bin/env python3
"""
Backup and recovery script for authentication system data
Handles secure backup of user data, sessions, and API keys
"""

import sqlite3
import json
import os
import shutil
import gzip
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import argparse
import sys
from pathlib import Path

class AuthDataBackup:
    def __init__(self, db_path: str = "/home/husni/project-permit-api/app.db"):
        self.db_path = db_path
        self.backup_dir = "/home/husni/project-permit-api/backups"
        self.encryption_key = os.getenv("BACKUP_ENCRYPTION_KEY", "default-key-change-in-production")

    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)

    def generate_backup_filename(self, backup_type: str) -> str:
        """Generate timestamped backup filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"auth_backup_{backup_type}_{timestamp}.json.gz"

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for backup (one-way)"""
        return hashlib.sha256(data.encode()).hexdigest()

    def backup_user_data(self) -> Dict:
        """Backup user data (excluding sensitive information)"""
        print("📦 Backing up user data...")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get user data (excluding passwords)
            cursor.execute("""
                SELECT id, email, name, created_at, updated_at, is_active, email_verified
                FROM users
            """)

            users = []
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                    "is_active": row[5],
                    "email_verified": row[6]
                })

            # Get user sessions
            cursor.execute("""
                SELECT id, user_id, session_token, created_at, expires_at, is_active
                FROM user_sessions
                WHERE is_active = 1
            """)

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "id": row[0],
                    "user_id": row[1],
                    "session_token_hash": self.hash_sensitive_data(row[2]),
                    "created_at": row[3],
                    "expires_at": row[4],
                    "is_active": row[5]
                })

            # Get API keys
            cursor.execute("""
                SELECT id, user_id, api_key_hash, name, created_at, expires_at, is_active, permissions
                FROM api_keys
                WHERE is_active = 1
            """)

            api_keys = []
            for row in cursor.fetchall():
                api_keys.append({
                    "id": row[0],
                    "user_id": row[1],
                    "api_key_hash": self.hash_sensitive_data(row[2]),
                    "name": row[3],
                    "created_at": row[4],
                    "expires_at": row[5],
                    "is_active": row[6],
                    "permissions": row[7]
                })

            conn.close()

            return {
                "users": users,
                "sessions": sessions,
                "api_keys": api_keys,
                "backup_timestamp": datetime.now().isoformat(),
                "total_users": len(users),
                "total_sessions": len(sessions),
                "total_api_keys": len(api_keys)
            }

        except Exception as e:
            print(f"❌ Error backing up user data: {e}")
            return {"error": str(e)}

    def backup_security_logs(self) -> Dict:
        """Backup security-related logs and events"""
        print("🔒 Backing up security logs...")

        try:
            log_files = [
                "/home/husni/project-permit-api/logs/app.log",
                "/home/husni/project-permit-api/logs/auth_monitor.log"
            ]

            security_logs = {}

            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        # Get last 1000 lines of security-related logs
                        lines = f.readlines()
                        security_lines = [
                            line for line in lines[-1000:]
                            if any(keyword in line.lower() for keyword in
                                ['auth', 'login', 'security', 'attack', 'suspicious', 'rate limit', 'failed'])
                        ]
                        security_logs[os.path.basename(log_file)] = security_lines

            return {
                "security_logs": security_logs,
                "backup_timestamp": datetime.now().isoformat(),
                "log_files_processed": len([f for f in log_files if os.path.exists(f)])
            }

        except Exception as e:
            print(f"❌ Error backing up security logs: {e}")
            return {"error": str(e)}

    def backup_configuration(self) -> Dict:
        """Backup authentication configuration"""
        print("⚙️  Backing up configuration...")

        try:
            config_files = [
                "/home/husni/project-permit-api/config.py",
                "/home/husni/project-permit-api/requirements.txt",
                "/home/husni/project-permit-api/runtime.txt"
            ]

            config_data = {}

            for config_file in config_files:
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read()
                        # Remove sensitive information
                        lines = content.split('\n')
                        sanitized_lines = []
                        for line in lines:
                            if any(sensitive in line.lower() for sensitive in
                                 ['password', 'secret', 'key', 'token']):
                                # Replace sensitive values with placeholders
                                parts = line.split('=')
                                if len(parts) == 2:
                                    sanitized_lines.append(f"{parts[0].strip()}=***REDACTED***")
                                else:
                                    sanitized_lines.append(line)
                            else:
                                sanitized_lines.append(line)

                        config_data[os.path.basename(config_file)] = '\n'.join(sanitized_lines)

            return {
                "configuration": config_data,
                "backup_timestamp": datetime.now().isoformat(),
                "config_files_processed": len([f for f in config_files if os.path.exists(f)])
            }

        except Exception as e:
            print(f"❌ Error backing up configuration: {e}")
            return {"error": str(e)}

    def create_full_backup(self) -> str:
        """Create a complete backup of all authentication data"""
        print("🔄 Creating full authentication backup...")

        self.ensure_backup_directory()

        # Collect all backup data
        backup_data = {
            "backup_type": "full_auth_backup",
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "user_data": self.backup_user_data(),
            "security_logs": self.backup_security_logs(),
            "configuration": self.backup_configuration()
        }

        # Generate backup filename
        backup_filename = self.generate_backup_filename("full")
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            # Compress and save backup
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)

            # Create backup metadata
            metadata = {
                "filename": backup_filename,
                "path": backup_path,
                "size_bytes": os.path.getsize(backup_path),
                "created_at": datetime.now().isoformat(),
                "checksum": self.calculate_checksum(backup_path),
                "contents": {
                    "users": backup_data["user_data"].get("total_users", 0),
                    "sessions": backup_data["user_data"].get("total_sessions", 0),
                    "api_keys": backup_data["user_data"].get("total_api_keys", 0)
                }
            }

            metadata_path = backup_path.replace('.json.gz', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)

            print(f"✅ Full backup created: {backup_path}")
            print(f"📊 Backup size: {metadata['size_bytes']} bytes")
            print(f"👥 Users backed up: {metadata['contents']['users']}")
            print(f"🔑 Sessions backed up: {metadata['contents']['sessions']}")
            print(f"🗝️  API keys backed up: {metadata['contents']['api_keys']}")

            return backup_path

        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return None

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        self.ensure_backup_directory()

        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith("auth_backup_") and file.endswith("_metadata.json"):
                metadata_path = os.path.join(self.backup_dir, file)
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        backups.append(metadata)
                except Exception as e:
                    print(f"Error reading backup metadata {file}: {e}")

        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups

    def restore_user_data(self, backup_path: str, restore_users: bool = True,
                         restore_sessions: bool = True, restore_api_keys: bool = True) -> bool:
        """Restore user data from backup"""
        print(f"🔄 Restoring data from: {backup_path}")

        try:
            # Load backup data
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            restored_counts = {"users": 0, "sessions": 0, "api_keys": 0}

            # Restore users
            if restore_users and "users" in backup_data.get("user_data", {}):
                users = backup_data["user_data"]["users"]
                for user in users:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO users
                            (id, email, name, created_at, updated_at, is_active, email_verified)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            user["id"], user["email"], user["name"],
                            user["created_at"], user["updated_at"],
                            user["is_active"], user["email_verified"]
                        ))
                        restored_counts["users"] += 1
                    except Exception as e:
                        print(f"Error restoring user {user['id']}: {e}")

            # Note: Sessions and API keys cannot be fully restored due to hashing
            # Only structural data can be restored, not actual tokens/keys

            conn.commit()
            conn.close()

            print(f"✅ Data restoration completed")
            print(f"👥 Users restored: {restored_counts['users']}")
            print("⚠️  Note: Sessions and API keys contain hashed data and cannot be fully restored")

            return True

        except Exception as e:
            print(f"❌ Error during restoration: {e}")
            return False

    def cleanup_old_backups(self, keep_days: int = 30):
        """Clean up old backups"""
        print(f"🧹 Cleaning up backups older than {keep_days} days...")

        self.ensure_backup_directory()
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)

        cleaned_count = 0
        for file in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, file)
            if os.path.getctime(file_path) < cutoff_date:
                try:
                    os.remove(file_path)
                    cleaned_count += 1
                    print(f"   Deleted: {file}")
                except Exception as e:
                    print(f"   Error deleting {file}: {e}")

        print(f"✅ Cleanup completed: {cleaned_count} old backups removed")

def main():
    parser = argparse.ArgumentParser(description="Authentication Data Backup and Recovery")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup"],
                       help="Action to perform")
    parser.add_argument("--backup-file", help="Backup file path for restore")
    parser.add_argument("--keep-days", type=int, default=30,
                       help="Days to keep backups during cleanup")
    parser.add_argument("--db-path", default="/home/husni/project-permit-api/app.db",
                       help="Database file path")

    args = parser.parse_args()

    backup_manager = AuthDataBackup(args.db_path)

    if args.action == "backup":
        print("🚀 Starting authentication data backup...")
        backup_path = backup_manager.create_full_backup()
        if backup_path:
            print(f"✅ Backup completed successfully: {backup_path}")
            sys.exit(0)
        else:
            print("❌ Backup failed")
            sys.exit(1)

    elif args.action == "list":
        print("📋 Available backups:")
        backups = backup_manager.list_backups()
        if not backups:
            print("   No backups found")
        else:
            for backup in backups:
                print(f"   📁 {backup['filename']}")
                print(f"      Created: {backup['created_at']}")
                print(f"      Size: {backup['size_bytes']} bytes")
                print(f"      Users: {backup['contents']['users']}")
                print(f"      Sessions: {backup['contents']['sessions']}")
                print(f"      API Keys: {backup['contents']['api_keys']}")
                print()

    elif args.action == "restore":
        if not args.backup_file:
            print("❌ --backup-file is required for restore action")
            sys.exit(1)

        backup_path = os.path.join(backup_manager.backup_dir, args.backup_file)
        if not os.path.exists(backup_path):
            print(f"❌ Backup file not found: {backup_path}")
            sys.exit(1)

        success = backup_manager.restore_user_data(backup_path)
        if success:
            print("✅ Data restoration completed")
            sys.exit(0)
        else:
            print("❌ Data restoration failed")
            sys.exit(1)

    elif args.action == "cleanup":
        backup_manager.cleanup_old_backups(args.keep_days)

if __name__ == "__main__":
    main()
