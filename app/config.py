from __future__ import annotations

from typing import Optional, List

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Mengelola semua pengaturan aplikasi secara terpusat.
    Secara otomatis memuat variabel dari environment atau file .env.
    """

    # Konfigurasi Pydantic untuk membaca dari file .env (hanya untuk development)
    model_config = SettingsConfigDict(
        env_file=".env" if __import__("os").getenv("ENVIRONMENT") != "production" else None,
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    # Pengaturan Aplikasi Umum
    APP_NAME: str = "Environmental Data Verification API"
    ENVIRONMENT: str = "development" # Or "production"
    LOG_LEVEL: str = "DEBUG" # Set to DEBUG for detailed logs
    GITHUB_REPO_URL: str = "https://github.com/hk-dev13"
    PORT: int = 8000

    # Konfigurasi API Eksternal
    # EPA Envirofacts
    EPA_ENV_BASE: str = "https://data.epa.gov/efservice/"
    EPA_ENV_TABLE: str = "tri_facility"

    # EPA CAMPD
    CAMPD_API_BASE_URL: str = "https://api.epa.gov/easey"
    CAMPD_API_KEY: Optional[str] = None

    # Logging
    LOG_FILE: Optional[str] = None

    #CORS Origins - Support multiple environment variable names for compatibility
    ALLOWED_ORIGINS: Optional[str] = None  # New Railway variable
    CORS_ALLOWED_ORIGINS: Optional[str] = None  # Alternative Railway variable

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins with priority: CORS_ALLOWED_ORIGINS > ALLOWED_ORIGINS"""
        if self.CORS_ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",")]
        elif self.ALLOWED_ORIGINS:
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        else:
            return ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]

    # Sumber Data ISO
    ISO_API_BASE: Optional[str] = None
    ISO_CSV_URL: Optional[str] = None
    ISO_XLSX_PATH: str = "reference/list_iso.xlsx"

    # Sumber Data EDGAR
    EDGAR_XLSX_PATH: str = "reference/EDGAR_emiss_on_UCDB_2024.xlsx"

    # Sumber Data Policy
    POLICY_XLSX_PATH: str = "reference/Annex III_Best practices and justifications.xlsx"

    # Keamanan & Kunci API
    # Daftar kunci API yang dipisahkan koma, format: "key1:App1:basic,key2:App2:premium"
    API_KEYS: Optional[str] = None
    MASTER_API_KEY: Optional[str] = None

    # Sentry Configuration
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0
    SENTRY_SEND_DEFAULT_PII: bool = True

    # Email Configuration
    EMAIL_SERVICE: str = "smtp"  # smtp, mailgun, sendgrid
    MAILGUN_API_KEY: Optional[str] = None
    MAILGUN_DOMAIN: Optional[str] = None
    MAILGUN_API_BASE_URL: str = "https://api.mailgun.net"
    SENDGRID_API_KEY: Optional[str] = None
    EMAIL_OFFLINE_MODE: bool = False

    # OAuth Configuration
    ENABLE_SOCIAL_AUTH: bool = True
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # OAuth Redirect URIs - Dynamic based on environment
    @property
    def google_redirect_uri(self) -> str:
        if self.ENVIRONMENT == "production":
            return "https://app.envoyou.com/auth/google/callback"
        else:
            return "http://localhost:3001/auth/google/callback"

    @property
    def github_redirect_uri(self) -> str:
        if self.ENVIRONMENT == "production":
            return "https://app.envoyou.com/auth/github/callback"
        else:
            return "http://localhost:3001/auth/github/callback"

    # For backward compatibility
    GOOGLE_REDIRECT_URI: str = "https://app.envoyou.com/auth/google/callback"
    GITHUB_REDIRECT_URI: str = "https://app.envoyou.com/auth/github/callback"

    # JWT Configuration
    JWT_SECRET_KEY: str  # Required - no default for security
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    ENABLE_SUPABASE_AUTH: bool = False

    @model_validator(mode='after')
    def set_production_defaults(self) -> 'Settings':
        """Set production-specific defaults based on ENVIRONMENT"""
        if self.ENVIRONMENT == "production":
            # Only set CORS defaults if no CORS variables are explicitly configured
            cors_configured = (
                self.CORS_ALLOWED_ORIGINS is not None or
                self.ALLOWED_ORIGINS is not None or
                (self.CORS_ORIGINS != ["*"] and self.CORS_ORIGINS != [])
            )

            if not cors_configured:
                self.CORS_ORIGINS = ["https://app.envoyou.com", "https://www.envoyou.com"]

            # More restrictive logging for production
            if hasattr(self, 'LOG_LEVEL') and self.LOG_LEVEL == "DEBUG":
                self.LOG_LEVEL = "INFO"

        return self


# Buat satu instance settings yang dapat digunakan kembali di seluruh aplikasi
settings = Settings()