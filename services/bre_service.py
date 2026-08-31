import logging
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from engine.context import BREContext
from engine.bre_engine import BREEngine, BREDecisionResult
from repositories.bre_rule_repository import BRERuleRepository
from models.lead_bre_result import LeadBREResult
from models.lead import Lead

logger = logging.getLogger("moneybeing.bre.service")


class BREService:
    def __init__(self, db: Session):
        self.db = db
        self.rule_repo = BRERuleRepository(db)

    def evaluate_context(self, context: BREContext) -> BREDecisionResult:
        # Load active rules ordered by priority ASC, id ASC from PostgreSQL
        active_rules = self.rule_repo.get_active_rules()
        logger.info(f"Loaded {len(active_rules)} active BRE rule(s) from database.")
        return BREEngine.evaluate(rules=active_rules, context=context)

    def evaluate_and_persist(
        self,
        lead_id: int,
        context: BREContext,
    ) -> Tuple[BREDecisionResult, List[LeadBREResult]]:
        decision = self.evaluate_context(context)

        persisted_results: List[LeadBREResult] = []
        for eval_res in decision.evaluations:
            result_record = LeadBREResult(
                lead_id=lead_id,
                rule_id=eval_res.rule_id,
                is_passed=eval_res.is_passed,
                failure_message=eval_res.failure_message,
            )
            self.db.add(result_record)
            persisted_results.append(result_record)

        self.db.flush()
        logger.info(f"Persisted {len(persisted_results)} evaluation result records for lead ID {lead_id}.")
        return decision, persisted_results
