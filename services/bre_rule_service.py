import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from models.bre_rule import BRERule
from models.audit_log import AuditLog
from repositories.bre_rule_repository import BRERuleRepository
from schemas.bre_rule import CreateBRERuleRequest, UpdateBRERuleRequest
from core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger("moneybeing.bre.rule_service")


class BRERuleService:
    def __init__(self, db: Session):
        self.db = db
        self.rule_repo = BRERuleRepository(db)

    def list_rules(self, is_active: Optional[bool] = None, field_name: Optional[str] = None) -> List[BRERule]:
        query = self.db.query(BRERule)
        if is_active is not None:
            query = query.filter(BRERule.is_active == is_active)
        if field_name:
            query = query.filter(BRERule.field_name == field_name.strip().lower())
        return query.order_by(BRERule.priority.asc(), BRERule.id.asc()).all()

    def get_rule_by_id(self, rule_id: int) -> BRERule:
        rule = self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise NotFoundException("BRE rule not found")
        return rule

    def create_rule(self, request: CreateBRERuleRequest, user_id: Optional[int] = None, ip_address: Optional[str] = None) -> BRERule:
        # Check duplicate active rule on identical field & operator
        existing = (
            self.db.query(BRERule)
            .filter(
                BRERule.field_name == request.field_name,
                BRERule.operator == request.operator,
                BRERule.rule_value == request.rule_value,
                BRERule.is_active == True,
            )
            .first()
        )
        if existing:
            raise ValidationException("An identical active BRE rule already exists")

        rule = self.rule_repo.create(
            rule_name=request.rule_name,
            field_name=request.field_name,
            operator=request.operator,
            rule_value=request.rule_value,
            failure_message=request.failure_message,
            is_active=request.is_active,
            priority=request.priority,
            created_by=user_id,
        )

        # Record Audit Log
        audit = AuditLog(
            user_id=user_id,
            action="CREATE",
            entity="BRE_RULE",
            entity_id=rule.id,
            new_value={
                "rule_name": rule.rule_name,
                "field_name": rule.field_name,
                "operator": rule.operator,
                "rule_value": rule.rule_value,
                "is_active": rule.is_active,
                "priority": rule.priority,
            },
            ip_address=ip_address,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)
        logger.info(f"Created BRE rule ID {rule.id} ('{rule.rule_name}') by User {user_id}")
        return rule

    def update_rule(
        self,
        rule_id: int,
        request: UpdateBRERuleRequest,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> BRERule:
        rule = self.get_rule_by_id(rule_id)

        old_value = {
            "rule_name": rule.rule_name,
            "field_name": rule.field_name,
            "operator": rule.operator,
            "rule_value": rule.rule_value,
            "failure_message": rule.failure_message,
            "is_active": rule.is_active,
            "priority": rule.priority,
        }

        # Apply updates
        if request.rule_name is not None:
            rule.rule_name = request.rule_name
        if request.field_name is not None:
            rule.field_name = request.field_name
        if request.operator is not None:
            rule.operator = request.operator
        if request.rule_value is not None:
            rule.rule_value = request.rule_value
        if request.failure_message is not None:
            rule.failure_message = request.failure_message
        if request.is_active is not None:
            rule.is_active = request.is_active
        if request.priority is not None:
            rule.priority = request.priority

        new_value = {
            "rule_name": rule.rule_name,
            "field_name": rule.field_name,
            "operator": rule.operator,
            "rule_value": rule.rule_value,
            "failure_message": rule.failure_message,
            "is_active": rule.is_active,
            "priority": rule.priority,
        }

        audit = AuditLog(
            user_id=user_id,
            action="UPDATE",
            entity="BRE_RULE",
            entity_id=rule.id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)
        logger.info(f"Updated BRE rule ID {rule.id} by User {user_id}")
        return rule

    def set_active_status(
        self,
        rule_id: int,
        is_active: bool,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> BRERule:
        rule = self.get_rule_by_id(rule_id)
        old_status = rule.is_active
        rule.is_active = is_active

        audit = AuditLog(
            user_id=user_id,
            action="ACTIVATE" if is_active else "DEACTIVATE",
            entity="BRE_RULE",
            entity_id=rule.id,
            old_value={"is_active": old_status},
            new_value={"is_active": is_active},
            ip_address=ip_address,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)
        logger.info(f"BRE rule ID {rule.id} status changed to {is_active} by User {user_id}")
        return rule
