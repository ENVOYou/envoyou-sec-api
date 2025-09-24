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
    print("Environmental Data Verification API Server")
    print("="*60)
    print(f"Server would start on http://localhost:{port}")
    print("Available endpoints:")
    print("  GET  /                     - API documentation")
    print("  GET  /health               - Health check")
    print("  POST /auth/register        - User registration")
    print("  POST /auth/set-password    - Set password for OAuth users")
    print("  POST /auth/login           - User login")
    print("  POST /auth/refresh         - Refresh access token")
    print("  POST /auth/logout          - User logout")
    print("  POST /auth/send-verification - Send email verification")
    print("  POST /auth/verify-email    - Verify email with token")
    print("  POST /auth/forgot-password - Request password reset")
    print("  POST /auth/reset-password  - Reset password with token")
    print("  POST /auth/change-password - Change password (authenticated)")
    print("  GET  /user/profile         - Get user profile (authenticated)")
    print("  PUT  /user/profile         - Update user profile (authenticated)")
    print("  POST /user/avatar          - Upload user avatar (authenticated)")
    print("  GET  /user/api-keys        - Get API keys (authenticated)")
    print("  POST /user/api-keys        - Create API key (authenticated)")
    print("  DELETE /user/api-keys/{id} - Delete API key (authenticated)")
    print("  GET  /user/sessions        - Get user sessions (authenticated)")
    print("  DELETE /user/sessions/{id} - Delete user session (authenticated)")
    print("  GET  /user/plan            - Get user plan (authenticated)")
    print("  POST /auth/2fa/setup       - Setup 2FA (authenticated)")
    print("  POST /auth/2fa/verify      - Verify 2FA (authenticated)")
    print("  POST /auth/2fa/disable     - Disable 2FA (authenticated)")
    print("  GET  /permits              - Get all permits")
    print("  GET  /permits/search       - Search permits")
    print("  GET  /permits/active       - Get active permits")
    print("  GET  /permits/company/<name> - Get permits by company")
    print("  GET  /permits/type/<type>  - Get permits by type")
    print("  GET  /permits/stats        - Get permit statistics")
    print("="*60)
    
    yield
    
    # Shutdown code (if needed)
    pass

app = FastAPI(
    title="Environmental Data Verification API",
    description="Production API for environmental data verification and compliance checking with multi-source data integration",
    version="1.0.0",
    contact={
            "name": "API Support",
            "email": "support@envoyou.com"
    },
    terms_of_service="https://j8w3vpxvpb.ap-southeast-2.awsapprunner.com/terms",
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
        "/auth/register", "/auth/set-password", "/auth/login", "/auth/refresh", "/auth/logout",
        "/auth/send-verification", "/auth/verify-email", "/auth/forgot-password", "/auth/reset-password",
        "/auth/2fa/setup", "/auth/2fa/verify", "/auth/2fa/disable",
        "/auth/google/login", "/auth/google/callback",
        "/auth/github/login", "/auth/github/callback"
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
        title="Environmental Data Verification API",
        version="1.0.0",
        description="Production API for environmental data verification and compliance checking with multi-source data integration",
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

# Register routers
app.include_router(health_router, prefix="/health")
app.include_router(permits_router, prefix="/permits")
# Terapkan dependensi API key dan rate limiting ke semua rute global
rate_limiter = rate_limit_dependency_factory()
app.include_router(global_router, prefix="/global", dependencies=[Depends(api_key_dependency), Depends(rate_limiter)])
app.include_router(admin_router, prefix="/admin")
app.include_router(auth_router, prefix="/auth")
app.include_router(supabase_auth_router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(cloudflare_router, prefix="/cloudflare")
# New v1 routers
app.include_router(audit_trail_router, prefix="/v1/audit")
app.include_router(export_router, prefix="/v1/export")
app.include_router(emissions_router, prefix="/v1/emissions")

@app.get("/", tags=["Health"])
async def home():
    api_info = {
        'name': 'Environmental Data Verification API',
        'version': '1.0.0',
        'description': 'Production API for environmental data verification and compliance checking with multi-source data integration',
        'endpoints': {
            '/': 'API information',
            '/health': 'Health check',
            '/permits': 'Get all permits',
            '/permits/search': 'Search permits by company name',
            '/permits/active': 'Get active permits only',
            '/permits/company/<company_name>': 'Get permits for specific company',
            '/permits/type/<permit_type>': 'Get permits by type',
            '/global/emissions': 'EPA emissions (filters: state, year, pollutant, page, limit)',
            '/global/emissions/stats': 'EPA emissions statistics',
            '/global/iso': 'ISO 14001 certifications (filters: country, limit)',
            '/global/eea': 'EEA indicators (filters: country, indicator, year, limit)',
            '/global/cevs/<company_name>': 'Compute CEVS score for a company (filters: country)',
            '/global/edgar': 'EDGAR series+trend (params: country, pollutant=PM2.5, window=3)',
            '/cloudflare/zones': 'Get Cloudflare zones (admin only)',
            '/cloudflare/dns': 'DNS record management (admin only)',
            '/cloudflare/security': 'Security settings management (admin only)',
            '/cloudflare/analytics': 'Zone analytics data (admin only)'
        },
        'usage_examples': {
            'get_all_permits': '/permits',
            'search_company': '/permits/search?nama=PT%20Pertamina',
            'get_active_permits': '/permits/active',
            'company_specific': '/permits/company/PT%20Semen%20Indonesia',
            'by_permit_type': '/permits/type/Izin%20Lingkungan',
            'epa_emissions': '/global/emissions?state=TX&year=2023&pollutant=CO2',
            'iso_cert': '/global/iso?country=DE&limit=5',
            'eea_indicator': '/global/eea?country=SE&indicator=GHG&year=2023&limit=5',
            'cevs_company': '/global/cevs/Green%20Energy%20Co?country=US',
            'cloudflare_zones': '/cloudflare/zones',
            'cloudflare_dns': '/cloudflare/dns?zone_id=zone123',
            'cloudflare_security': '/cloudflare/security?zone_id=zone123',
            'cloudflare_analytics': '/cloudflare/analytics?zone_id=zone123&since=1h'
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
                '/', '/health', '/permits', '/permits/search', '/permits/active',
                '/permits/company/<company_name>', '/permits/type/<permit_type>',
                '/permits/stats', '/global/emissions', '/global/emissions/stats',
                '/global/iso', '/global/eea', '/global/cevs/<company_name>', '/global/edgar',
                '/cloudflare/zones', '/cloudflare/dns', '/cloudflare/security', '/cloudflare/analytics'
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
