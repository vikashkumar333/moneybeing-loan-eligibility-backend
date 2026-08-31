import logging
from typing import List, Sequence
from pydantic import BaseModel, Field
from engine.context import BREContext
from engine.rule_evaluator import RuleEvaluationResult, evaluate_single_rule
from models.bre_rule import BRERule
from core.constants import BREStatus

logger = logging.getLogger("moneybeing.bre.engine")


class BREDecisionResult(BaseModel):
    status: str = Field(..., description="Eligible or Not Eligible")
    passed_rules: int = Field(..., description="Number of rules passed")
    failed_rules: int = Field(..., description="Number of rules failed")
    rejection_reasons: List[str] = Field(default_factory=list, description="List of failed rule messages")
    evaluations: List[RuleEvaluationResult] = Field(default_factory=list, description="Individual rule evaluation results")


class BREEngine:
    @staticmethod
    def evaluate(rules: Sequence[BRERule], context: BREContext) -> BREDecisionResult:
        logger.info(f"BRE Engine starting evaluation of {len(rules)} active rule(s)...")
        evaluations: List[RuleEvaluationResult] = []
        rejection_reasons: List[str] = []

        passed_count = 0
        failed_count = 0

        for rule in rules:
            if not rule.is_active:
                continue

            eval_result = evaluate_single_rule(
                rule_id=rule.id,
                rule_name=rule.rule_name,
                field_name=rule.field_name,
                operator=rule.operator,
                rule_value=rule.rule_value,
                failure_message=rule.failure_message,
                context=context,
            )
            evaluations.append(eval_result)

            if eval_result.is_passed:
                passed_count += 1
            else:
                failed_count += 1
                if eval_result.failure_message and eval_result.failure_message not in rejection_reasons:
                    rejection_reasons.append(eval_result.failure_message)

        is_eligible = (failed_count == 0)
        decision_status = BREStatus.ELIGIBLE.value if is_eligible else BREStatus.NOT_ELIGIBLE.value

        logger.info(f"BRE Decision: {decision_status} (Passed: {passed_count}, Failed: {failed_count})")
        return BREDecisionResult(
            status=decision_status,
            passed_rules=passed_count,
            failed_rules=failed_count,
            rejection_reasons=rejection_reasons,
            evaluations=evaluations,
        )
