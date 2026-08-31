from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


class BRERule(Base):
    __tablename__ = "bre_rules"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True, autoincrement=True)
    rule_name = Column(String(100), nullable=False)
    field_name = Column(String(50), nullable=False)
    operator = Column(String(10), nullable=False)
    rule_value = Column(String(100), nullable=False)
    failure_message = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    priority = Column(Integer, nullable=False, default=1, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("priority > 0", name="chk_bre_rule_priority_positive"),
        CheckConstraint("operator IN ('>=', '<=', '>', '<', '==', '!=')", name="chk_bre_rule_operator"),
        Index("idx_bre_rule_active_priority", "is_active", "priority"),
    )

    # Relationships
    creator = relationship("User", back_populates="created_bre_rules")
    lead_results = relationship("LeadBREResult", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<BRERule(id={self.id}, name='{self.rule_name}', field='{self.field_name}', op='{self.operator}', val='{self.rule_value}')>"
