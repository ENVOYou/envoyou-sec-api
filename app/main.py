from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

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
from app.routes import admin, global_data, health, permits, external

app.include_router(admin.router, prefix="/admin")
app.include_router(global_data.router, prefix="/global")
app.include_router(health.router, prefix="/health")
app.include_router(permits.router, prefix="/permits")
app.include_router(external.router, prefix="/external")

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}