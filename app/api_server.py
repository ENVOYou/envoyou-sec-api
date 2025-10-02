from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    from app.models.database import create_tables
    create_tables()
    
    port = settings.PORT # Use settings for port
    print("="*60)
    print("Envoyou SEC Compliance API Server")
    print("="*60)
    print(f"Server running on port {port}")
    print("Focus: SEC Climate Disclosure (Scope 1 & 2)")
    print("")
    print("Available endpoints:")
    print("  GET  /                     - API information")
    print("  GET  /health               - Health check")
    print("")
    print("🔐 Authentication (Supabase):")
    print("  POST /v1/auth/login        - User login")
    print("  POST /v1/auth/register     - User registration")
    print("  POST /v1/auth/supabase/verify - Supabase token verification")
    print("  GET  /v1/user/profile      - User profile")
    print("  GET  /v1/user/api-keys     - API key management")
    print("")
    print("SEC Compliance API:")
    print("  POST /v1/emissions/calculate - Calculate Scope 1 & 2 emissions")
    print("  GET  /v1/emissions/factors   - Get emission factors")
    print("  POST /v1/validation/epa      - EPA cross-validation")
    print("  POST /v1/export/sec/package  - Generate SEC filing package")
    print("  POST /v1/admin/mappings      - Company-facility mapping (admin)")
    print("  GET  /v1/audit               - Audit trail (admin)")
    print("")
    print("="*60)
    
    yield
    
    # Shutdown code (if needed)
    pass

app = FastAPI(
    title="Envoyou SEC Compliance API",
    description="SEC Climate Disclosure compliance API with auditable emissions calculation and EPA validation",
    version="1.0.0",
    contact={
            "name": "API Support",
            "email": "support@envoyou.com"
    },
    terms_of_service="https://envoyou.com/terms",
    lifespan=lifespan
)

# Ensure uploads directory exists
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/avatars", exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS
import logging
import os
from app.config import settings # Import settings object

# Load environment variables

# Import blueprints as routers for FastAPI
from app.routes import health_router
from app.routes.permits import router as permits_router
from app.routes.global_data import router as global_router
from app.routes.admin import router as admin_router
from app.routes.auth import router as auth_router
from app.routes.user import router as user_router
from app.routes.supabase_auth import router as supabase_auth_router
from app.routes.cloudflare import router as cloudflare_router
from app.routes.contact import router as contact_router
from app.routes.audit_trail import router as audit_trail_router
from app.routes.export import router as export_router
from app.routes.emissions import router as emissions_router
from app.routes.validation import router as validation_router
from app.routes.admin_mapping import router as admin_mapping_router
from app.routes.emissions_factors import router as emissions_factors_router
from app.routes.user_extended import router as user_extended_router
from app.routes.agents import router as agents_router
from app.routes.recaptcha import router as recaptcha_router
from app.routes.developer import router as developer_router

# Import security utilities
from app.utils.security import is_public_endpoint, validate_api_key, rate_limit_dependency_factory
from app.utils.security_middleware import SecurityMiddleware

# CORS
cors_origins = settings.cors_origins_list  # Use the new property that handles multiple env vars
if cors_origins != ['*'] and isinstance(cors_origins, list):
    # Already parsed by the property
    pass
else:
    cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins, # Use the parsed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Requested-With"],
)

# GZIP for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000) # Keep this as is

# Security middleware for XSS, CSRF, and input sanitization
app.add_middleware(SecurityMiddleware)

# Rate limiting middleware
from app.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Logging
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO) # Use settings.LOG_LEVEL
log_handlers = []
if settings.LOG_FILE: # Use settings for LOG_FILE
    log_handlers.append(logging.FileHandler(settings.LOG_FILE, mode='a'))
log_handlers.append(logging.StreamHandler())
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers,
    force=True  # Force re-configuration to override Uvicorn's default logger
)

# Explicitly set Uvicorn's loggers to the desired level
logging.getLogger("uvicorn").setLevel(log_level)
logging.getLogger("uvicorn.access").setLevel(log_level)
logging.getLogger("uvicorn.error").setLevel(log_level)
logger = logging.getLogger(__name__)

async def api_key_dependency(request: Request):
    public_paths = [
        "/health", "/", "/docs", "/openapi.json", "/redoc",
        "/v1/auth/register", "/v1/auth/set-password", "/v1/auth/login", "/v1/auth/refresh", "/v1/auth/logout",
        "/v1/auth/send-verification", "/v1/auth/verify-email", "/v1/auth/forgot-password", "/v1/auth/reset-password",
        "/v1/auth/2fa/setup", "/v1/auth/2fa/verify", "/v1/auth/2fa/disable",
        "/v1/auth/google/login", "/v1/auth/google/callback",
        "/v1/auth/github/login", "/v1/auth/github/callback",
        "/v1/auth/supabase/verify", "/v1/auth/supabase/me",
        "/v1/verify-recaptcha"
        ]
    path = request.url.path
    if not any(path == pub_path or path.startswith(pub_path + "/") for pub_path in public_paths):
        if path.startswith("/global"):
            api_key = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
            elif request.headers.get("X-API-Key"):
                api_key = request.headers.get("X-API-Key")
            elif request.query_params.get("api_key"):
                api_key = request.query_params.get("api_key")
            if not api_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "status": "error",
                        "message": "API key required for global data access. Include it in Authorization header (Bearer token), X-API-Key header, or api_key parameter.",
                        "code": "MISSING_API_KEY",
                        "demo_keys": {
                            "basic": "demo_key_basic_2025",
                            "premium": "demo_key_premium_2025"
                        }
                    }
                )
            client_info = validate_api_key(api_key)
            if not client_info:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "status": "error",
                        "message": "Invalid API key",
                        "code": "INVALID_API_KEY"
                    }
                )
            request.state.client_info = client_info
            request.state.api_key = api_key

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Envoyou SEC Compliance API",
        version="1.0.0",
        description="SEC Climate Disclosure compliance API with auditable emissions calculation and EPA validation",
        routes=app.routes,
        tags=[
            {"name": "Health", "description": "Service health and status endpoints"},
            {"name": "Authentication", "description": "User authentication and account management endpoints"},
            {"name": "User Profile", "description": "User profile management endpoints"},
            {"name": "API Keys", "description": "API key management endpoints"},
            {"name": "Sessions", "description": "User session management endpoints"},
            {"name": "Two-Factor Auth", "description": "Two-factor authentication endpoints"},
            {"name": "Global Data", "description": "Global environmental data endpoints"},
            {"name": "Admin", "description": "Administrative and statistics endpoints"}
        ]
    )
    api_key_scheme = {
        "type": "apiKey",
        "in": "header",
        "name": "Authorization",
        "description": "Enter: Bearer your_api_key"
    }
    openapi_schema["securityDefinitions"] = {"ApiKeyAuth": api_key_scheme}
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Register routers - SEC API focused
app.include_router(health_router)

# Authentication & User Management (for frontend integration)
app.include_router(supabase_auth_router, prefix="/v1/auth")
app.include_router(user_router, prefix="/v1/user")

# Core SEC API endpoints
app.include_router(audit_trail_router, prefix="/v1/audit")
app.include_router(export_router, prefix="/v1/export")
app.include_router(emissions_router, prefix="/v1/emissions")
app.include_router(emissions_factors_router, prefix="/v1/emissions")
app.include_router(validation_router, prefix="/v1/validation")
app.include_router(admin_mapping_router, prefix="/v1/admin")
app.include_router(user_extended_router, prefix="/v1/user")
app.include_router(developer_router, prefix="/v1/developer")

# AI Agents endpoints
app.include_router(agents_router, prefix="/v1/agents")

# reCAPTCHA verification endpoint used by frontend
app.include_router(recaptcha_router, prefix="/v1/verify-recaptcha")

# Legacy endpoints (disabled for SEC API focus)
# app.include_router(permits_router, prefix="/permits")
# app.include_router(global_router, prefix="/global", dependencies=[Depends(api_key_dependency), Depends(rate_limiter)])
# app.include_router(admin_router, prefix="/admin")
# app.include_router(auth_router, prefix="/auth")
# app.include_router(cloudflare_router, prefix="/cloudflare")

@app.get("/", tags=["Health"])
async def home():
    api_info = {
        'name': 'Envoyou SEC Compliance API',
        'version': '1.0.0',
        'description': 'SEC Climate Disclosure compliance API with auditable emissions calculation and EPA validation',
        'focus': 'SEC Climate Disclosure (Scope 1 & 2)',
        'endpoints': {
            '/': 'API information',
            '/health': 'Health check',
            '/v1/auth/login': 'User authentication (Supabase)',
            '/v1/auth/register': 'User registration (Supabase)',
            '/v1/auth/supabase/verify': 'Supabase token verification',
            '/v1/user/profile': 'User profile management',
            '/v1/user/api-keys': 'API key management',
            '/v1/user/calculations': 'Calculation history',
            '/v1/user/packages': 'SEC package management',
            '/v1/user/notifications': 'User notifications',
            '/v1/user/preferences': 'User preferences',
            '/v1/user/activity': 'Activity log',
            '/v1/emissions/calculate': 'Calculate Scope 1 & 2 emissions',
            '/v1/emissions/factors': 'Get emission factors',
            '/v1/emissions/units': 'Get supported units',
            '/v1/validation/epa': 'EPA cross-validation',
            '/v1/export/sec/cevs/{company}': 'Export CEVS data',
            '/v1/export/sec/package': 'Generate SEC filing package',
            '/v1/admin/mappings': 'Company-facility mapping (admin)',
            '/v1/audit': 'Audit trail management (admin)',
            '/v1/agents/full-workflow': 'AI-powered full compliance workflow',
            '/v1/agents/validate-and-score': 'AI data validation and scoring',
            '/v1/agents/status': 'AI agents status and information'
        },
        'usage_examples': {
            'calculate_emissions': '/v1/emissions/calculate',
            'get_factors': '/v1/emissions/factors',
            'epa_validation': '/v1/validation/epa',
            'sec_export': '/v1/export/sec/package',
            'audit_trail': '/v1/audit'
        },
        'authentication': {
            'supabase': 'JWT token from Supabase auth for user endpoints',
            'api_key': 'X-API-Key header required for SEC API endpoints',
            'demo_key': 'demo_key (for testing SEC endpoints)'
        },
        'frontend_integration': {
            'app_url': 'https://app.envoyou.com',
            'docs_url': 'https://docs.envoyou.com',
            'auth_provider': 'Supabase'
        }
    }
    return api_info

@app.exception_handler(404)
async def not_found(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
        'status': 'error',
            'message': 'Endpoint not found',
            'available_endpoints': [
                '/', '/health',
                '/v1/auth/login', '/v1/auth/register', '/v1/auth/supabase/verify', '/v1/user/profile', '/v1/user/api-keys',
                '/v1/user/calculations', '/v1/user/packages', '/v1/user/notifications', '/v1/user/preferences', '/v1/user/activity',
                '/v1/emissions/calculate', '/v1/emissions/factors', '/v1/emissions/units',
                '/v1/validation/epa',
                '/v1/export/sec/cevs/{company}', '/v1/export/sec/package',
                '/v1/admin/mappings', '/v1/audit',
                '/v1/agents/full-workflow', '/v1/agents/validate-and-score', '/v1/agents/status'
            ]
        }
    )

@app.exception_handler(500)
async def internal_error(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            'status': 'error',
        'message': 'Internal server error'
        }
    )
