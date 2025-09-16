from app.routes.health import router as health_router
from app.routes.admin import router as admin_router
from app.routes.global_data import router as global_router
from app.routes.permits import router as permits_router
from app.routes.contact import router as contact_router

__all__ = ["health_router", "admin_router", "global_router", "permits_router", "contact_router"]

