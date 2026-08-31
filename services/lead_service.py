import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.lead import Lead
from models.lead_bre_result import LeadBREResult
from repositories.lead_repository import LeadRepository
from services.credit_score_service import CreditScoreService
from services.bre_service import BREService
from engine.context import BREContext
from schemas.lead import CreateLeadRequest, LeadResponse
from core.exceptions import DuplicateEntityException, ProviderException
from core.constants import BREStatus

logger = logging.getLogger("moneybeing.lead.service")


class LeadService:
    def __init__(
        self,
        db: Session,
        credit_score_service: Optional[CreditScoreService] = None,
        bre_service: Optional[BREService] = None,
    ):
        self.db = db
        self.lead_repo = LeadRepository(db)
        self.credit_score_service = credit_score_service or CreditScoreService()
        self.bre_service = bre_service or BREService(db)

    async def create_and_evaluate_lead(self, request: CreateLeadRequest) -> LeadResponse:
        # 1. Application-level Duplicate Mobile Check
        existing_lead = self.lead_repo.get_by_mobile(request.mobile)
        if existing_lead:
            logger.warning(f"Duplicate lead submission attempted for mobile: ...{request.mobile[-4:]}")
            raise DuplicateEntityException("Lead already exists")

        # 2. Fetch Credit Score from configured Provider
        credit_result = await self.credit_score_service.fetch_credit_score(
            mobile=request.mobile,
            name=request.full_name,
        )
        if not credit_result.success or credit_result.credit_score is None:
            logger.error(f"Credit score retrieval failed: {credit_result.error_code} - {credit_result.message}")
            raise ProviderException("Credit score service is temporarily unavailable.")

        credit_score = credit_result.credit_score

        # 3. Construct BRE Context and evaluate active rules
        bre_context = BREContext(
            date_of_birth=request.date_of_birth,
            monthly_income=request.monthly_income,
            credit_score=credit_score,
            loan_amount=request.loan_amount,
            property_value=request.property_value,
            employment_type=request.employment_type,
            loan_type=request.loan_type,
        )
        decision = self.bre_service.evaluate_context(bre_context)

        # 4. Atomic Database Transaction: Persist Lead + LeadBREResults
        try:
            lead = Lead(
                full_name=request.full_name,
                mobile=request.mobile,
                email=request.email,
                date_of_birth=request.date_of_birth,
                city=request.city,
                pincode=request.pincode,
                loan_type=request.loan_type,
                employment_type=request.employment_type,
                monthly_income=request.monthly_income,
                loan_amount=request.loan_amount,
                property_value=request.property_value,
                credit_score=credit_score,
                bre_status=decision.status,
                rejection_reasons=decision.rejection_reasons if decision.rejection_reasons else None,
            )
            self.db.add(lead)
            self.db.flush()  # Populates lead.id

            # Persist per-rule evaluations
            for eval_res in decision.evaluations:
                bre_res_record = LeadBREResult(
                    lead_id=lead.id,
                    rule_id=eval_res.rule_id,
                    is_passed=eval_res.is_passed,
                    failure_message=eval_res.failure_message,
                )
                self.db.add(bre_res_record)

            self.db.commit()
            self.db.refresh(lead)
            logger.info(f"Lead ID {lead.id} created successfully with status [{lead.bre_status}].")

        except IntegrityError as e:
            self.db.rollback()
            logger.warning(f"Database IntegrityError on lead creation: {e.orig}")
            if "mobile" in str(e.orig).lower() or "unique" in str(e.orig).lower():
                raise DuplicateEntityException("Lead already exists")
            raise

        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected database transaction error: {str(e)}")
            raise

        # 5. Formulate API Response
        reasons_list = decision.rejection_reasons if (decision.status != BREStatus.ELIGIBLE.value and decision.rejection_reasons) else None

        return LeadResponse(
            status="success",
            lead_id=lead.id,
            credit_score=credit_score,
            bre_status=lead.bre_status,
            reasons=reasons_list,
        )
