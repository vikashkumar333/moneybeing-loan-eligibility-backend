from typing import Optional, List, Tuple
from datetime import date, datetime, time
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc, asc
from models.lead import Lead
from models.lead_bre_result import LeadBREResult

ALLOWED_SORT_FIELDS = {
    "created_at": Lead.created_at,
    "updated_at": Lead.updated_at,
    "full_name": Lead.full_name,
    "credit_score": Lead.credit_score,
    "loan_amount": Lead.loan_amount,
    "bre_status": Lead.bre_status,
}


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, lead_id: int) -> Optional[Lead]:
        return self.db.query(Lead).filter(Lead.id == lead_id).first()

    def get_by_id_with_results(self, lead_id: int) -> Optional[Lead]:
        return (
            self.db.query(Lead)
            .options(joinedload(Lead.bre_results))
            .filter(Lead.id == lead_id)
            .first()
        )

    def get_by_mobile(self, mobile: str) -> Optional[Lead]:
        return self.db.query(Lead).filter(Lead.mobile == mobile).first()

    def create(self, **kwargs) -> Lead:
        lead = Lead(**kwargs)
        self.db.add(lead)
        self.db.flush()
        return lead

    def create_lead_with_bre_results(
        self,
        full_name: str,
        mobile: str,
        date_of_birth: date,
        city: str,
        pincode: str,
        loan_type: str,
        employment_type: str,
        monthly_income: Decimal,
        loan_amount: Decimal,
        property_value: Decimal,
        credit_score: Optional[int] = None,
        bre_status: str = "Eligible",
        rejection_reasons: Optional[list] = None,
        email: Optional[str] = None,
        bre_evaluations: Optional[List[dict]] = None,
    ) -> Lead:
        lead = Lead(
            full_name=full_name,
            mobile=mobile,
            email=email,
            date_of_birth=date_of_birth,
            city=city,
            pincode=pincode,
            loan_type=loan_type,
            employment_type=employment_type,
            monthly_income=monthly_income,
            loan_amount=loan_amount,
            property_value=property_value,
            credit_score=credit_score,
            bre_status=bre_status,
            rejection_reasons=rejection_reasons,
        )
        self.db.add(lead)
        self.db.flush()

        if bre_evaluations:
            for eval_data in bre_evaluations:
                bre_res = LeadBREResult(
                    lead_id=lead.id,
                    rule_id=eval_data.get("rule_id"),
                    is_passed=eval_data.get("is_passed", False),
                    failure_message=eval_data.get("failure_message"),
                )
                self.db.add(bre_res)
            self.db.flush()

        return lead

    def get_paginated_leads(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        loan_type: Optional[str] = None,
        employment_type: Optional[str] = None,
        bre_status: Optional[str] = None,
        city: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Lead], int]:
        query = self.db.query(Lead)

        # 1. Search filter
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Lead.full_name.ilike(search_pattern),
                    Lead.mobile.ilike(search_pattern),
                    Lead.email.ilike(search_pattern),
                )
            )

        # 2. Specific filters
        if loan_type:
            query = query.filter(Lead.loan_type.ilike(loan_type.strip()))
        if employment_type:
            query = query.filter(Lead.employment_type.ilike(employment_type.strip()))
        if bre_status:
            query = query.filter(Lead.bre_status.ilike(bre_status.strip()))
        if city:
            query = query.filter(Lead.city.ilike(f"%{city.strip()}%"))

        # 3. Date range filters
        if date_from:
            dt_from = datetime.combine(date_from, time.min)
            query = query.filter(Lead.created_at >= dt_from)
        if date_to:
            dt_to = datetime.combine(date_to, time.max)
            query = query.filter(Lead.created_at <= dt_to)

        # 4. Total count
        total = query.count()

        # 5. Sorting
        sort_col = ALLOWED_SORT_FIELDS.get(sort_by, Lead.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_col))
        else:
            query = query.order_by(desc(sort_col))

        # 6. Pagination
        offset = (page - 1) * page_size
        leads = query.offset(offset).limit(page_size).all()

        return leads, total

    # Backward compatibility alias
    def list_leads(self, **kwargs) -> Tuple[List[Lead], int]:
        return self.get_paginated_leads(**kwargs)
