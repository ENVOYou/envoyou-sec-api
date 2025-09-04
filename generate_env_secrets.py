#!/usr/bin/env python3
"""
Envoyou CEVS API - Environment Configuration Generator
=====================================================

Script untuk secara otomatis menggenerate nilai-nilai secure untuk file .env
termasuk SECRET_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY, dan SESSION_SECRET.

Usage:
    python generate_env_secrets.py [--backup] [--force]

Options:
    --backup: Buat backup file .env sebelum mengganti
    --force:  Force replace tanpa konfirmasi

Author: GitHub Copilot
Date: September 4, 2025
"""

import os
import sys
import secrets
import string
import argparse
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet


class EnvSecretGenerator:
    """Generator untuk nilai-nilai rahasia dalam file .env"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.backup_suffix = f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def generate_secret_key(self, length: int = 32) -> str:
        """Generate SECRET_KEY dengan panjang tertentu"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def generate_jwt_secret(self, length: int = 32) -> str:
        """Generate JWT_SECRET_KEY dengan panjang 32 karakter (minimum)"""
        return secrets.token_hex(length // 2)  # token_hex menghasilkan 2x panjang

    def generate_encryption_key(self) -> str:
        """Generate ENCRYPTION_KEY menggunakan Fernet (32 bytes)"""
        return Fernet.generate_key().decode()

    def generate_session_secret(self, length: int = 32) -> str:
        """Generate SESSION_SECRET"""
        return secrets.token_urlsafe(length)

    def generate_api_key(self, prefix: str = "api", length: int = 32) -> str:
        """Generate API key dengan prefix"""
        random_part = secrets.token_hex(length // 2)
        return f"{prefix}_{random_part}"

    def read_env_file(self) -> str:
        """Baca isi file .env"""
        if not self.env_file.exists():
            print(f"❌ File {self.env_file} tidak ditemukan!")
            return ""

        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error membaca file: {e}")
            return ""

    def write_env_file(self, content: str) -> bool:
        """Tulis konten ke file .env"""
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Error menulis file: {e}")
            return False

    def create_backup(self) -> bool:
        """Buat backup file .env"""
        if not self.env_file.exists():
            return False

        backup_file = self.env_file.with_suffix(self.backup_suffix)
        try:
            with open(self.env_file, 'r', encoding='utf-8') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print(f"✅ Backup dibuat: {backup_file}")
            return True
        except Exception as e:
            print(f"❌ Error membuat backup: {e}")
            return False

    def replace_placeholders(self, content: str) -> str:
        """Ganti placeholder dengan nilai-nilai yang di-generate"""
        replacements = {
            'your_flask_secret_key_here_change_this_in_production': self.generate_secret_key(32),
            'your_super_secret_jwt_key_here_change_this_32_chars_min': self.generate_jwt_secret(32),
            'your_32_character_encryption_key_here': self.generate_encryption_key(),
            'your_session_secret_here_change_this': self.generate_session_secret(32),
            'your_super_secret_master_key_change_this_in_production': self.generate_api_key("master", 32),
            'your_db_password': self.generate_secret_key(16),
            'your_app_password': self.generate_secret_key(16),
        }

        for placeholder, new_value in replacements.items():
            if placeholder in content:
                content = content.replace(placeholder, new_value)
                print(f"🔄 Replaced: {placeholder[:30]}... -> {new_value[:20]}...")

        return content

    def generate_all_secrets(self, backup: bool = True, force: bool = False) -> bool:
        """Generate semua secrets dan update file .env"""
        print("🚀 Starting Environment Secret Generation...")
        print("=" * 50)

        # Baca file .env
        content = self.read_env_file()
        if not content:
            return False

        # Buat backup jika diminta
        if backup:
            if not self.create_backup():
                if not force:
                    print("❌ Backup gagal. Gunakan --force untuk melanjutkan tanpa backup.")
                    return False

        # Ganti placeholder
        print("\n🔐 Generating secure secrets...")
        new_content = self.replace_placeholders(content)

        # Tulis file baru
        if self.write_env_file(new_content):
            print("\n✅ File .env berhasil diupdate dengan secrets baru!")
            print("⚠️  IMPORTANT: Simpan secrets ini di tempat yang aman!")
            print("🔒 Jangan commit file .env ke repository!")
            return True
        else:
            print("\n❌ Gagal mengupdate file .env")
            return False

    def show_generated_secrets(self) -> None:
        """Tampilkan contoh secrets yang akan di-generate"""
        print("🔍 Preview Generated Secrets:")
        print("=" * 40)
        print(f"SECRET_KEY: {self.generate_secret_key(32)}")
        print(f"JWT_SECRET_KEY: {self.generate_jwt_secret(32)}")
        print(f"ENCRYPTION_KEY: {self.generate_encryption_key()}")
        print(f"SESSION_SECRET: {self.generate_session_secret(32)}")
        print(f"MASTER_API_KEY: {self.generate_api_key('master', 32)}")
        print("=" * 40)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Generate secure secrets for .env file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_env_secrets.py              # Generate with backup
  python generate_env_secrets.py --no-backup  # Generate without backup
  python generate_env_secrets.py --force      # Force replace without confirmation
  python generate_env_secrets.py --preview    # Show what will be generated
        """
    )

    parser.add_argument('--no-backup', action='store_true',
                       help='Skip creating backup file')
    parser.add_argument('--force', action='store_true',
                       help='Force replace without confirmation')
    parser.add_argument('--preview', action='store_true',
                       help='Show preview of generated secrets')
    parser.add_argument('--env-file', default='.env',
                       help='Path to .env file (default: .env)')

    args = parser.parse_args()

    # Initialize generator
    generator = EnvSecretGenerator(args.env_file)

    if args.preview:
        # Show preview only
        generator.show_generated_secrets()
        return

    # Confirm action
    if not args.force:
        print("⚠️  This will replace secrets in your .env file.")
        if args.no_backup:
            print("⚠️  No backup will be created!")
        else:
            print("✅ A backup will be created automatically.")

        response = input("\nContinue? (y/N): ").lower().strip()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled.")
            return

    # Generate secrets
    backup = not args.no_backup
    success = generator.generate_all_secrets(backup=backup, force=args.force)

    if success:
        print("\n🎉 Environment secrets generated successfully!")
        print("📝 Next steps:")
        print("   1. Review the generated secrets in .env")
        print("   2. Test your application")
        print("   3. Save secrets securely (password manager, etc.)")
        print("   4. Never commit .env to version control")
    else:
        print("\n❌ Failed to generate environment secrets!")
        sys.exit(1)


if __name__ == "__main__":
    main()
