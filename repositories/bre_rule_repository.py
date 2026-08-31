from typing import Optional, List
from sqlalchemy.orm import Session
from models.bre_rule import BRERule


class BRERuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, rule_id: int) -> Optional[BRERule]:
        return self.db.query(BRERule).filter(BRERule.id == rule_id).first()

    def get_active_rules(self) -> List[BRERule]:
        return (
            self.db.query(BRERule)
            .filter(BRERule.is_active == True)
            .order_by(BRERule.priority.asc(), BRERule.id.asc())
            .all()
        )

    def list_all(self) -> List[BRERule]:
        return self.db.query(BRERule).order_by(BRERule.priority.asc(), BRERule.id.asc()).all()

    def create(
        self,
        rule_name: str,
        field_name: str,
        operator: str,
        rule_value: str,
        failure_message: str,
        priority: int = 1,
        is_active: bool = True,
        created_by: Optional[int] = None,
    ) -> BRERule:
        rule = BRERule(
            rule_name=rule_name,
            field_name=field_name,
            operator=operator,
            rule_value=rule_value,
            failure_message=failure_message,
            priority=priority,
            is_active=is_active,
            created_by=created_by,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update(self, rule_id: int, **kwargs) -> Optional[BRERule]:
        rule = self.get_by_id(rule_id)
        if not rule:
            return None
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def set_active_status(self, rule_id: int, is_active: bool) -> Optional[BRERule]:
        return self.update(rule_id, is_active=is_active)
