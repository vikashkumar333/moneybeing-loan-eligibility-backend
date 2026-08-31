import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from pydantic import BaseModel
from engine.context import BREContext
from engine.operator_registry import evaluate_operator
from core.exceptions import AppException

logger = logging.getLogger("moneybeing.bre.evaluator")


class RuleEvaluationResult(BaseModel):
    rule_id: Optional[int]
    rule_name: str
    field_name: str
    operator: str
    target_value: str
    actual_value: Optional[str]
    is_passed: bool
    failure_message: Optional[str]


def format_failure_message(failure_message: Optional[str], field_name: str, target_value: str, actual_value: Any) -> str:
    if not failure_message or not failure_message.strip():
        return f"{field_name} does not meet requirement (Target: {target_value}, Actual: {actual_value})"
    
    msg = failure_message.strip()
    # Support dynamic template placeholders
    msg = msg.replace("{threshold}", str(target_value))
    msg = msg.replace("{target}", str(target_value))
    msg = msg.replace("{rule_value}", str(target_value))
    msg = msg.replace("{value}", str(target_value))
    msg = msg.replace("{actual}", str(actual_value))
    return msg


def evaluate_single_rule(
    rule_id: Optional[int],
    rule_name: str,
    field_name: str,
    operator: str,
    rule_value: str,
    failure_message: str,
    context: BREContext,
) -> RuleEvaluationResult:
    # 1. Resolve field from context
    is_supported, actual_value = context.resolve_field(field_name)
    if not is_supported:
        logger.warning(f"Unsupported field '{field_name}' in rule '{rule_name}'")
        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            field_name=field_name,
            operator=operator,
            target_value=rule_value,
            actual_value=None,
            is_passed=False,
            failure_message=f"Unsupported rule field: '{field_name}'",
        )

    if actual_value is None:
        logger.info(f"Missing context value for field '{field_name}' in rule '{rule_name}'")
        formatted_fail_msg = format_failure_message(failure_message, field_name, rule_value, actual_value)
        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            field_name=field_name,
            operator=operator,
            target_value=rule_value,
            actual_value=None,
            is_passed=False,
            failure_message=formatted_fail_msg or f"Missing required applicant value for '{field_name}'",
        )

    # 2. Type cast rule_value matching actual_value type
    try:
        if isinstance(actual_value, int):
            parsed_target = int(Decimal(rule_value.strip()))
        elif isinstance(actual_value, Decimal):
            parsed_target = Decimal(rule_value.strip())
        elif isinstance(actual_value, float):
            parsed_target = float(rule_value.strip())
        else:
            parsed_target = str(rule_value.strip())
    except (ValueError, InvalidOperation):
        logger.warning(f"Invalid rule_value '{rule_value}' for field '{field_name}' in rule '{rule_name}'")
        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            field_name=field_name,
            operator=operator,
            target_value=rule_value,
            actual_value=str(actual_value),
            is_passed=False,
            failure_message=f"Invalid configured rule threshold: '{rule_value}'",
        )

    # 3. Perform comparison
    try:
        is_passed = evaluate_operator(operator, actual_value, parsed_target)
    except Exception as e:
        logger.warning(f"Error evaluating operator '{operator}' on rule '{rule_name}': {e}")
        return RuleEvaluationResult(
            rule_id=rule_id,
            rule_name=rule_name,
            field_name=field_name,
            operator=operator,
            target_value=rule_value,
            actual_value=str(actual_value),
            is_passed=False,
            failure_message=f"Evaluation error: {str(e)}",
        )

    final_failure_msg = None if is_passed else format_failure_message(failure_message, field_name, str(parsed_target), actual_value)

    return RuleEvaluationResult(
        rule_id=rule_id,
        rule_name=rule_name,
        field_name=field_name,
        operator=operator,
        target_value=rule_value,
        actual_value=str(actual_value),
        is_passed=is_passed,
        failure_message=final_failure_msg,
    )
