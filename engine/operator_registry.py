import operator
from typing import Any, Callable, Dict
from core.exceptions import AppException


class UnsupportedOperatorException(AppException):
    def __init__(self, op_symbol: str):
        super().__init__(message=f"Unsupported BRE operator: '{op_symbol}'", status_code=400)


OPERATOR_MAP: Dict[str, Callable[[Any, Any], bool]] = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}


def evaluate_operator(op_symbol: str, left: Any, right: Any) -> bool:
    clean_op = op_symbol.strip()
    op_func = OPERATOR_MAP.get(clean_op)
    if not op_func:
        raise UnsupportedOperatorException(clean_op)
    return op_func(left, right)
