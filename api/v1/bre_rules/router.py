from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User
from api.v1.auth.dependencies import require_admin
from services.bre_rule_service import BRERuleService
from schemas.bre_rule import (
    CreateBRERuleRequest,
    UpdateBRERuleRequest,
    ToggleStatusRequest,
    BRERuleDetailResponse,
)
from core.responses import APIResponse

router = APIRouter(prefix="/bre-rules", tags=["BRE Rule Management"])


@router.get("", response_model=APIResponse[List[BRERuleDetailResponse]], summary="List All BRE Rules (Admin)")
def list_rules(
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    field_name: Optional[str] = Query(default=None, description="Filter by field name"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule_service = BRERuleService(db)
    rules = rule_service.list_rules(is_active=is_active, field_name=field_name)
    data = [BRERuleDetailResponse.model_validate(r) for r in rules]
    return APIResponse(status="success", data=data)


@router.post("", response_model=APIResponse[BRERuleDetailResponse], status_code=status.HTTP_201_CREATED, summary="Create New BRE Rule (Admin)")
def create_rule(
    request: CreateBRERuleRequest,
    http_req: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule_service = BRERuleService(db)
    ip_address = http_req.client.host if http_req.client else None
    rule = rule_service.create_rule(request, user_id=current_user.id, ip_address=ip_address)
    return APIResponse(status="success", message="BRE rule created successfully", data=BRERuleDetailResponse.model_validate(rule))


@router.get("/{rule_id}", response_model=APIResponse[BRERuleDetailResponse], summary="Get BRE Rule Details (Admin)")
def get_rule(
    rule_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule_service = BRERuleService(db)
    rule = rule_service.get_rule_by_id(rule_id)
    return APIResponse(status="success", data=BRERuleDetailResponse.model_validate(rule))


@router.put("/{rule_id}", response_model=APIResponse[BRERuleDetailResponse], summary="Update BRE Rule (Admin)")
def update_rule(
    rule_id: int,
    request: UpdateBRERuleRequest,
    http_req: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule_service = BRERuleService(db)
    ip_address = http_req.client.host if http_req.client else None
    rule = rule_service.update_rule(rule_id, request, user_id=current_user.id, ip_address=ip_address)
    return APIResponse(status="success", message="BRE rule updated successfully", data=BRERuleDetailResponse.model_validate(rule))


@router.delete("/{rule_id}", response_model=APIResponse[dict], summary="Deactivate BRE Rule (Admin)")
def delete_rule(
    rule_id: int,
    http_req: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule_service = BRERuleService(db)
    ip_address = http_req.client.host if http_req.client else None
    rule_service.set_active_status(rule_id, is_active=False, user_id=current_user.id, ip_address=ip_address)
    return APIResponse(status="success", message="BRE rule deactivated successfully")


@router.patch("/{rule_id}/status", response_model=APIResponse[BRERuleDetailResponse], summary="Toggle BRE Rule Active Status (Admin)")
def toggle_status(
    rule_id: int,
    request: ToggleStatusRequest,
    http_req: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule_service = BRERuleService(db)
    ip_address = http_req.client.host if http_req.client else None
    rule = rule_service.set_active_status(rule_id, is_active=request.is_active, user_id=current_user.id, ip_address=ip_address)
    return APIResponse(status="success", message=f"BRE rule {'activated' if request.is_active else 'deactivated'} successfully", data=BRERuleDetailResponse.model_validate(rule))
