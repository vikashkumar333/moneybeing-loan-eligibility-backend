from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User
from api.v1.auth.dependencies import require_admin
from services.dashboard_service import DashboardService
from schemas.dashboard import DashboardStatsResponse, LeadDistributionResponse
from core.responses import APIResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=APIResponse[DashboardStatsResponse], summary="Get Aggregated Dashboard Statistics (Admin)")
def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    dashboard_service = DashboardService(db)
    stats = dashboard_service.get_stats()
    return APIResponse(status="success", data=stats)


@router.get("/lead-distribution", response_model=APIResponse[LeadDistributionResponse], summary="Get Lead Distribution Breakdown (Admin)")
def get_lead_distribution(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    dashboard_service = DashboardService(db)
    dist = dashboard_service.get_distribution()
    return APIResponse(status="success", data=dist)
