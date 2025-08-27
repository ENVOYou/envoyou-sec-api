from fastapi import FastAPI
from app.routes import admin, global_data, health, permits

app = FastAPI(
    title="Environmental Data Verification API",
    description="Production API for environmental data verification and compliance checking with multi-source data integration",
    version="1.0.0",
)

# Register routers
app.include_router(admin.router, prefix="/admin")
app.include_router(global_data.router, prefix="/global")
app.include_router(health.router, prefix="/health")
app.include_router(permits.router, prefix="/permits")

@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}