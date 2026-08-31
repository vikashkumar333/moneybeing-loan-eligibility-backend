from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Index, Integer, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class LeadBREResult(Base):
    __tablename__ = "lead_bre_results"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    lead_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("bre_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    is_passed = Column(Boolean, nullable=False)
    failure_message = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_lead_bre_lead_rule", "lead_id", "rule_id"),
    )

    # Relationships
    lead = relationship("Lead", back_populates="bre_results")
    rule = relationship("BRERule", back_populates="lead_results")

    def __repr__(self) -> str:
        return f"<LeadBREResult(lead_id={self.lead_id}, rule_id={self.rule_id}, passed={self.is_passed})>"
