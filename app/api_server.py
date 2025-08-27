from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import blueprints as routers for FastAPI
from app.routes import health_router
from app.routes.permits import router as permits_router
from app.routes.global_data import router as global_router
from app.routes.admin import router as admin_router

# Import security utilities
from app.utils.security import setup_rate_limiting, is_public_endpoint, validate_api_key

app = FastAPI(
    title="Environmental Data Verification API",
    description="Production API for environmental data verification and compliance checking with multi-source data integration",
    version="1.0.0",
    contact={
            "name": "API Support",
            "email": "support@environmentalapi.com"
    },
    terms_of_service="https://j8w3vpxvpb.ap-southeast-2.awsapprunner.com/terms"
)

# CORS
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins != '*' and isinstance(cors_origins, str):
    cors_origins = [origin.strip() for origin in cors_origins.split(",")]
else:
    cors_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# GZIP for response compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Logging
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO)
log_handlers = []
if os.getenv('LOG_FILE'):
    log_handlers.append(logging.FileHandler(os.getenv('LOG_FILE'), mode='a'))
log_handlers.append(logging.StreamHandler())
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# Mount static files for docs if needed
app.mount("/flasgger_static", StaticFiles(directory="flasgger_static"), name="flasgger_static")

async def api_key_dependency(request: Request):
    public_paths = [
        "/health", "/", "/docs", "/openapi.json", "/redoc"
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
app.include_router(health_router)
app.include_router(permits_router, prefix="")
app.include_router(global_router, prefix="", dependencies=[Depends(api_key_dependency)])
app.include_router(admin_router, prefix="")

@app.get("/", tags=["Health"])
async def home():
    api_info = {
        'name': 'KLHK Permit API Proxy',
        'version': '1.0.0',
        'description': 'API proxy untuk mengakses data perizinan PTSP MENLHK',
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
            '/global/edgar': 'EDGAR series+trend (params: country, pollutant=PM2.5, window=3)'
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
            'cevs_company': '/global/cevs/Green%20Energy%20Co?country=US'
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
                '/global/iso', '/global/eea', '/global/cevs/<company_name>', '/global/edgar'
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

@app.on_event("startup")
async def print_startup_info():
    port = int(os.environ.get('PORT', 8000))
    print("="*60)
    print("🚀 KLHK Permit API Proxy Server")
    print("="*60)
    print(f"Server would start on http://localhost:{port}")
    print("Available endpoints:")
    print("  GET  /                     - API documentation")
    print("  GET  /health               - Health check")
    print("  GET  /permits              - Get all permits")
    print("  GET  /permits/search       - Search permits")
    print("  GET  /permits/active       - Get active permits")
    print("  GET  /permits/company/<name> - Get permits by company")
    print("  GET  /permits/type/<type>  - Get permits by type")
    print("  GET  /permits/stats        - Get permit statistics")
    print("="*60)

