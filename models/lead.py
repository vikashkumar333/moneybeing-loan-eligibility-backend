from sqlalchemy import BigInteger, CheckConstraint, Column, Date, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(100), nullable=False, index=True)
    mobile = Column(String(15), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    loan_type = Column(String(30), nullable=False, index=True)
    employment_type = Column(String(30), nullable=False)
    monthly_income = Column(Numeric(15, 2), nullable=False)
    loan_amount = Column(Numeric(15, 2), nullable=False)
    property_value = Column(Numeric(15, 2), nullable=False)
    credit_score = Column(Integer, nullable=True, index=True)
    bre_status = Column(String(30), nullable=True, index=True)
    rejection_reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("monthly_income >= 0", name="chk_lead_monthly_income_positive"),
        CheckConstraint("loan_amount > 0", name="chk_lead_loan_amount_positive"),
        CheckConstraint("property_value > 0", name="chk_lead_property_value_positive"),
        CheckConstraint("(credit_score IS NULL) OR (credit_score >= 300 AND credit_score <= 900)", name="chk_lead_credit_score_range"),
        CheckConstraint("loan_type IN ('HOME_LOAN', 'LAP', 'Home Loan', 'Loan Against Property')", name="chk_lead_loan_type"),
        CheckConstraint("employment_type IN ('SALARIED', 'SELF_EMPLOYED', 'Salaried', 'Self Employed')", name="chk_lead_employment_type"),
        CheckConstraint("bre_status IS NULL OR bre_status IN ('ELIGIBLE', 'NOT_ELIGIBLE', 'PENDING', 'Eligible', 'Not Eligible', 'Pending')", name="chk_lead_bre_status"),
        Index("idx_lead_created_status", "created_at", "bre_status"),
    )

    # Relationships
    bre_results = relationship("LeadBREResult", back_populates="lead", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, name='{self.full_name}', mobile='{self.mobile}', bre_status='{self.bre_status}')>"
