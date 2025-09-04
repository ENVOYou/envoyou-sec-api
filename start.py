#!/usr/bin/env python3
"""
Production startup script for Envoyou CEVS API
Optimized for Render deployment
"""

import os
import sys
import uvicorn
from pathlib import Path

def setup_production_environment():
    """Setup environment for production deployment"""

    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Set production defaults if not set
    env_defaults = {
        "PORT": "10000",
        "LOG_LEVEL": "INFO",
        "ENVIRONMENT": "production",
        "DEBUG": "false",
        "CORS_ORIGINS": "https://envoyou.com,https://your-frontend-domain.com",
    }

    for key, default_value in env_defaults.items():
        if not os.getenv(key):
            os.environ[key] = default_value
            print(f"Set {key}={default_value}")

    # Ensure critical paths exist
    reference_files = [
        "reference/EDGAR_emiss_on_UCDB_2024.xlsx",
        "reference/list_iso.xlsx",
        "reference/Annex III_Best practices and justifications.xlsx"
    ]

    for file_path in reference_files:
        if not Path(file_path).exists():
            print(f"Warning: {file_path} not found")

    print("✅ Production environment setup complete")

def main():
    """Main startup function"""
    print("🚀 Starting Envoyou CEVS API - Production Mode")
    print("=" * 50)

    # Setup environment
    setup_production_environment()

    # Get port from environment
    port = int(os.getenv("PORT", "10000"))
    host = os.getenv("HOST", "0.0.0.0")
    workers = int(os.getenv("WEB_CONCURRENCY", "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    print(f"📡 Server Configuration:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   Log Level: {log_level}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
    print()

    # Start server
    try:
        uvicorn.run(
            "app.api_server:app",
            host=host,
            port=port,
            workers=workers,
            log_level=log_level,
            access_log=True,
            server_header=False,  # Don't expose server info
            date_header=False,    # Don't expose date for caching
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
