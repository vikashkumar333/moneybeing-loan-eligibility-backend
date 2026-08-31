from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User
from schemas.lead import CreateLeadRequest, LeadResponse, LeadListItem, LeadDetailResponse
from services.lead_service import LeadService
from repositories.lead_repository import LeadRepository
from api.v1.auth.dependencies import require_admin
from core.responses import APIResponse, PaginatedResponse
from core.exceptions import NotFoundException

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED, summary="Create Loan Lead & Evaluate Eligibility")
async def create_lead(
    request: CreateLeadRequest,
    db: Session = Depends(get_db),
):
    lead_service = LeadService(db)
    return await lead_service.create_and_evaluate_lead(request)


@router.get("", response_model=PaginatedResponse[LeadListItem], summary="List Leads (Admin Protected)")
def list_leads(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(default=None, description="Search by name, mobile, or email"),
    loan_type: Optional[str] = Query(default=None, description="Filter by loan type"),
    employment_type: Optional[str] = Query(default=None, description="Filter by employment type"),
    bre_status: Optional[str] = Query(default=None, description="Filter by BRE status: Eligible / Not Eligible"),
    city: Optional[str] = Query(default=None, description="Filter by city"),
    date_from: Optional[date] = Query(default=None, description="Filter leads created on/after date (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(default=None, description="Filter leads created on/before date (YYYY-MM-DD)"),
    sort_by: str = Query(default="created_at", description="Sort field: created_at, updated_at, full_name, credit_score, loan_amount, bre_status"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$", description="Sort direction: asc or desc"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    lead_repo = LeadRepository(db)
    leads, total = lead_repo.get_paginated_leads(
        page=page,
        page_size=page_size,
        search=search,
        loan_type=loan_type,
        employment_type=employment_type,
        bre_status=bre_status,
        city=city,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items = [LeadListItem.model_validate(lead) for lead in leads]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get("/{lead_id}", response_model=APIResponse[LeadDetailResponse], summary="Get Lead Details (Admin Protected)")
def get_lead_detail(
    lead_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    lead_repo = LeadRepository(db)
    lead = lead_repo.get_by_id_with_results(lead_id)
    if not lead:
        raise NotFoundException("Lead not found")

    detail = LeadDetailResponse.model_validate(lead)
    return APIResponse(status="success", data=detail)
