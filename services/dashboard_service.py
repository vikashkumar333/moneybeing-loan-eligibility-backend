import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from models.lead import Lead
from schemas.dashboard import DashboardStatsResponse, LeadDistributionResponse
from core.constants import BREStatus

logger = logging.getLogger("moneybeing.dashboard.service")


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> DashboardStatsResponse:
        # Aggregation query
        row = (
            self.db.query(
                func.count(Lead.id).label("total_leads"),
                func.sum(
                    case((Lead.bre_status == BREStatus.ELIGIBLE.value, 1), else_=0)
                ).label("eligible_leads"),
                func.sum(
                    case((Lead.bre_status == BREStatus.NOT_ELIGIBLE.value, 1), else_=0)
                ).label("rejected_leads"),
                func.avg(Lead.credit_score).label("avg_credit_score"),
            )
            .first()
        )

        total_leads = int(row.total_leads or 0)
        eligible_leads = int(row.eligible_leads or 0)
        rejected_leads = int(row.rejected_leads or 0)
        avg_score = float(round(row.avg_credit_score, 2)) if row.avg_credit_score is not None else None

        return DashboardStatsResponse(
            total_leads=total_leads,
            eligible_leads=eligible_leads,
            rejected_leads=rejected_leads,
            average_credit_score=avg_score,
        )

    def get_distribution(self) -> LeadDistributionResponse:
        # By loan type
        loan_types_res = (
            self.db.query(Lead.loan_type, func.count(Lead.id))
            .group_by(Lead.loan_type)
            .all()
        )
        by_loan_type = {k: count for k, count in loan_types_res if k}

        # By employment type
        emp_types_res = (
            self.db.query(Lead.employment_type, func.count(Lead.id))
            .group_by(Lead.employment_type)
            .all()
        )
        by_emp_type = {k: count for k, count in emp_types_res if k}

        # Status counts
        stats = self.get_stats()

        return LeadDistributionResponse(
            eligible_count=stats.eligible_leads,
            not_eligible_count=stats.rejected_leads,
            by_loan_type=by_loan_type,
            by_employment_type=by_emp_type,
        )
