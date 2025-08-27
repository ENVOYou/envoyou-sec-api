from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI(
    title="Environmental Data Verification API",
    description="Production API for environmental data verification and compliance checking with multi-source data integration",
    version="1.0.0",
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
from app.routes import admin, global_data, health, permits

app.include_router(admin.router, prefix="/admin")
app.include_router(global_data.router, prefix="/global")
app.include_router(health.router, prefix="/health")
app.include_router(permits.router, prefix="/permits")

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}