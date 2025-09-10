from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Initialize Sentry for error monitoring
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from app.config import settings

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=settings.SENTRY_SEND_DEFAULT_PII,
        integrations=[
            FastApiIntegration(),
            HttpxIntegration(),
        ],
        # Performance monitoring
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        # Release health tracking
        enable_tracing=True,
        environment=settings.ENVIRONMENT,
    )
    print("✅ Sentry error monitoring initialized")
else:
    print("⚠️  Sentry DSN not configured, error monitoring disabled")

app = FastAPI(
    title="Environmental Data Verification API",
    description="Production API for environmental data verification and compliance checking with multi-source data integration",
    version="1.0.0",
)

# Add CORS middleware to allow frontend connections
origins = [
    "http://localhost:5173",  # Vite dev server default
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Alternative port
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Join all error messages into one string
    error_messages = ", ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": error_messages},
    )

# Import and include routers
from app.routes import admin, auth, global_data, health, permits, external, supabase_auth
from app.routes.user import router as user_router
from app.routers.notification_router import router as notification_router

app.include_router(admin.router, prefix="/admin")
app.include_router(auth.router, prefix="/auth")
app.include_router(global_data.router, prefix="/global")
app.include_router(health.router, prefix="/health")
app.include_router(permits.router, prefix="/permits")
app.include_router(external.router, prefix="/external")
app.include_router(supabase_auth.router, prefix="/auth")
app.include_router(user_router, prefix="/user")
app.include_router(notification_router)

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}