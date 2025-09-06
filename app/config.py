from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Mengelola semua pengaturan aplikasi secara terpusat.
    Secara otomatis memuat variabel dari environment atau file .env.
    """

    # Konfigurasi Pydantic untuk membaca dari file .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
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

    #CORS Origins
    CORS_ORIGINS: str = "*"

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


# Buat satu instance settings yang dapat digunakan kembali di seluruh aplikasi
settings = Settings()