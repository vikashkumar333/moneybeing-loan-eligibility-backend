from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User
from engine.context import BREContext
from services.bre_service import BREService
from schemas.bre import BREEvaluateRequest, BREDecisionResponse
from api.v1.auth.dependencies import get_current_user
from core.responses import APIResponse

router = APIRouter(prefix="/bre", tags=["Business Rule Engine"])


@router.post("/evaluate", response_model=APIResponse[BREDecisionResponse], summary="Test BRE Rule Evaluation")
def evaluate_bre_context(
    request: BREEvaluateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    context = BREContext(
        date_of_birth=request.date_of_birth,
        monthly_income=request.monthly_income,
        credit_score=request.credit_score,
        loan_amount=request.loan_amount,
        property_value=request.property_value,
        employment_type=request.employment_type,
        loan_type=request.loan_type,
    )
    bre_service = BREService(db)
    decision = bre_service.evaluate_context(context)

    return APIResponse(
        status="success",
        data=BREDecisionResponse(
            status=decision.status,
            passed_rules=decision.passed_rules,
            failed_rules=decision.failed_rules,
            rejection_reasons=decision.rejection_reasons,
            evaluations=decision.evaluations,
        ),
    )
