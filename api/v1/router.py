from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine
from app.dependencies import get_redis_client
from core.responses import APIResponse
from api.v1.auth.router import router as auth_router
from api.v1.bre.router import router as bre_router
from api.v1.leads.router import router as leads_router
from api.v1.dashboard.router import router as dashboard_router
from api.v1.bre_rules.router import router as bre_rules_router

api_router = APIRouter()

# Mount API Routers
api_router.include_router(auth_router)
api_router.include_router(bre_router)
api_router.include_router(leads_router)
api_router.include_router(dashboard_router)
api_router.include_router(bre_rules_router)


@api_router.get("/health", response_model=APIResponse[dict], tags=["System"])
def health_check():
    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    redis_client = get_redis_client()
    redis_status = "healthy" if redis_client else "offline (bypass active)"

    return APIResponse(
        status="success",
        message="MoneyBeing API v1 is operational",
        data={
            "api_version": "v1",
            "database": db_status,
            "redis": redis_status,
        },
    )
