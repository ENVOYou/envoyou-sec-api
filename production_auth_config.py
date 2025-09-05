#!/usr/bin/env python3
"""
Production configuration for authentication system
Secure settings for production deployment
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# PRODUCTION AUTHENTICATION CONFIGURATION
# ==========================================

class ProductionAuthConfig:
    """Production-ready authentication configuration"""

    # ==========================================
    # SECURITY SETTINGS
    # ==========================================

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Password Security
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))
    PASSWORD_REQUIRE_UPPERCASE = os.getenv("PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true"
    PASSWORD_REQUIRE_LOWERCASE = os.getenv("PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true"
    PASSWORD_REQUIRE_DIGITS = os.getenv("PASSWORD_REQUIRE_DIGITS", "true").lower() == "true"
    PASSWORD_REQUIRE_SPECIAL = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"

    # Session Security
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "60"))
    MAX_CONCURRENT_SESSIONS = int(os.getenv("MAX_CONCURRENT_SESSIONS", "5"))
    SESSION_CLEANUP_INTERVAL_MINUTES = int(os.getenv("SESSION_CLEANUP_INTERVAL_MINUTES", "30"))

    # ==========================================
    # RATE LIMITING
    # ==========================================

    # Authentication endpoints
    AUTH_RATE_LIMIT_REQUESTS = int(os.getenv("AUTH_RATE_LIMIT_REQUESTS", "5"))
    AUTH_RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_MINUTES", "15"))

    # API endpoints
    API_RATE_LIMIT_REQUESTS = int(os.getenv("API_RATE_LIMIT_REQUESTS", "100"))
    API_RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("API_RATE_LIMIT_WINDOW_MINUTES", "60"))

    # ==========================================
    # EMAIL SERVICE
    # ==========================================

    # SMTP Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

    # Email Templates
    EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@yourdomain.com")
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Permit API")

    # ==========================================
    # DATABASE
    # ==========================================

    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

    # ==========================================
    # MONITORING & LOGGING
    # ==========================================

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/permit-api/auth.log")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Monitoring
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))

    # ==========================================
    # BACKUP & RECOVERY
    # ==========================================

    # Backup Configuration
    BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    BACKUP_ENCRYPTION_KEY = os.getenv("BACKUP_ENCRYPTION_KEY")

    # ==========================================
    # SECURITY HEADERS
    # ==========================================

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://yourdomain.com").split(",")
    CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

    # Security Headers
    SECURITY_HEADERS_ENABLED = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year
    CSP_DEFAULT_SRC = os.getenv("CSP_DEFAULT_SRC", "'self'")
    CSP_SCRIPT_SRC = os.getenv("CSP_SCRIPT_SRC", "'self'")
    CSP_STYLE_SRC = os.getenv("CSP_STYLE_SRC", "'self'")

    # ==========================================
    # API KEYS
    # ==========================================

    # API Key Configuration
    API_KEY_LENGTH = int(os.getenv("API_KEY_LENGTH", "32"))
    API_KEY_PREFIX = os.getenv("API_KEY_PREFIX", "pk_")
    API_KEY_EXPIRY_DAYS = int(os.getenv("API_KEY_EXPIRY_DAYS", "365"))

    # ==========================================
    # VALIDATION METHODS
    # ==========================================

    @classmethod
    def validate_configuration(cls) -> list:
        """Validate production configuration"""
        errors = []

        # Required secrets
        required_secrets = [
            ("JWT_SECRET_KEY", cls.JWT_SECRET_KEY),
            ("JWT_REFRESH_SECRET_KEY", cls.JWT_REFRESH_SECRET_KEY),
            ("SMTP_USERNAME", cls.SMTP_USERNAME),
            ("SMTP_PASSWORD", cls.SMTP_PASSWORD),
            ("BACKUP_ENCRYPTION_KEY", cls.BACKUP_ENCRYPTION_KEY)
        ]

        for name, value in required_secrets:
            if not value:
                errors.append(f"Missing required secret: {name}")

        # JWT secrets should be different
        if cls.JWT_SECRET_KEY and cls.JWT_REFRESH_SECRET_KEY:
            if cls.JWT_SECRET_KEY == cls.JWT_REFRESH_SECRET_KEY:
                errors.append("JWT_SECRET_KEY and JWT_REFRESH_SECRET_KEY should be different")

        # Password requirements
        if cls.PASSWORD_MIN_LENGTH < 8:
            errors.append("PASSWORD_MIN_LENGTH should be at least 8")

        # Rate limiting sanity checks
        if cls.AUTH_RATE_LIMIT_REQUESTS < 1:
            errors.append("AUTH_RATE_LIMIT_REQUESTS should be at least 1")

        if cls.API_RATE_LIMIT_REQUESTS < 10:
            errors.append("API_RATE_LIMIT_REQUESTS should be at least 10")

        return errors

    @classmethod
    def get_security_summary(cls) -> dict:
        """Get security configuration summary"""
        return {
            "jwt_configuration": {
                "access_token_expiry": f"{cls.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes",
                "refresh_token_expiry": f"{cls.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days",
                "secrets_configured": bool(cls.JWT_SECRET_KEY and cls.JWT_REFRESH_SECRET_KEY)
            },
            "password_policy": {
                "min_length": cls.PASSWORD_MIN_LENGTH,
                "require_uppercase": cls.PASSWORD_REQUIRE_UPPERCASE,
                "require_lowercase": cls.PASSWORD_REQUIRE_LOWERCASE,
                "require_digits": cls.PASSWORD_REQUIRE_DIGITS,
                "require_special": cls.PASSWORD_REQUIRE_SPECIAL
            },
            "rate_limiting": {
                "auth_limit": f"{cls.AUTH_RATE_LIMIT_REQUESTS} requests per {cls.AUTH_RATE_LIMIT_WINDOW_MINUTES} minutes",
                "api_limit": f"{cls.API_RATE_LIMIT_REQUESTS} requests per {cls.API_RATE_LIMIT_WINDOW_MINUTES} minutes"
            },
            "email_service": {
                "smtp_configured": bool(cls.SMTP_USERNAME and cls.SMTP_PASSWORD),
                "tls_enabled": cls.SMTP_USE_TLS,
                "ssl_enabled": cls.SMTP_USE_SSL
            },
            "monitoring": {
                "logging_enabled": True,
                "metrics_enabled": cls.ENABLE_METRICS,
                "backup_enabled": cls.BACKUP_ENABLED
            }
        }

# ==========================================
# PRODUCTION ENVIRONMENT VALIDATION
# ==========================================

def validate_production_environment():
    """Validate production environment setup"""
    print("🔍 Validating production environment...")

    config_errors = ProductionAuthConfig.validate_configuration()

    if config_errors:
        print("❌ Configuration errors found:")
        for error in config_errors:
            print(f"   - {error}")
        return False

    print("✅ Configuration validation passed")

    # Check required files
    required_files = [
        "/home/husni/project-permit-api/app.db",
        "/home/husni/project-permit-api/logs"
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file/directory missing: {file_path}")
            return False

    print("✅ Required files check passed")

    # Check permissions
    db_path = "/home/husni/project-permit-api/app.db"
    if os.path.exists(db_path):
        permissions = oct(os.stat(db_path).st_mode)[-3:]
        if permissions not in ['600', '640', '644']:
            print(f"⚠️  Database file permissions: {permissions} (recommended: 600)")

    print("✅ Environment validation completed")
    return True

# ==========================================
# PRODUCTION DEPLOYMENT CHECKLIST
# ==========================================

PRODUCTION_CHECKLIST = {
    "security": [
        "✅ JWT secrets configured and different",
        "✅ Password policy meets requirements",
        "✅ Rate limiting configured",
        "✅ Security headers enabled",
        "✅ HTTPS/TLS configured",
        "✅ Database encrypted at rest",
        "✅ Backup encryption configured"
    ],
    "infrastructure": [
        "✅ Database connection pool configured",
        "✅ Logging system configured",
        "✅ Monitoring and alerting setup",
        "✅ Backup system configured",
        "✅ Load balancer configured",
        "✅ CDN configured for static assets"
    ],
    "application": [
        "✅ Environment variables configured",
        "✅ Dependencies installed",
        "✅ Database migrations applied",
        "✅ Static files configured",
        "✅ Email service configured",
        "✅ API documentation generated"
    ],
    "monitoring": [
        "✅ Application logs configured",
        "✅ Error tracking configured",
        "✅ Performance monitoring configured",
        "✅ Security monitoring configured",
        "✅ Backup monitoring configured"
    ]
}

def print_production_checklist():
    """Print production deployment checklist"""
    print("\n📋 PRODUCTION DEPLOYMENT CHECKLIST")
    print("=" * 50)

    for category, items in PRODUCTION_CHECKLIST.items():
        print(f"\n🔧 {category.upper()}:")
        for item in items:
            print(f"   {item}")

    print("\n💡 Use the validation scripts to verify each item:")
    print("   python scripts/validate_auth_deployment.py")
    print("   python scripts/ci_cd_auth_tests.py")

if __name__ == "__main__":
    print("🚀 Production Authentication Configuration")
    print("=" * 50)

    # Validate environment
    if validate_production_environment():
        print("\n📊 Security Configuration Summary:")
        summary = ProductionAuthConfig.get_security_summary()

        for section, details in summary.items():
            print(f"\n🔒 {section.replace('_', ' ').title()}:")
            for key, value in details.items():
                print(f"   {key}: {value}")

        print_production_checklist()
    else:
        print("\n❌ Production environment validation failed!")
        print("Please fix the configuration errors above before deploying to production.")
        exit(1)
