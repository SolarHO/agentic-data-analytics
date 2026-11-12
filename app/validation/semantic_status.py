
from enum import Enum

from app.graph.metric_plan import MetricPlan
from app.validation.sql_semantic_validator import (
    validate_metric_semantics,
)


class SemanticStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"


# 현재 Validator가 명시적으로 검출하는
# 비즈니스 규칙 위반 메시지
INVALID_ERROR_PATTERNS = (
    "delivered status missing",
    "actual delivery date null check missing",
    "delay comparison missing",
    "invalid or extra population conditions",
    "invalid calculation formula",
    "Missing metric column",
    "Outer output columns do not match",
    "Duplicate output alias",
    "incorrect source column",
    "invalid CTE qualifier",
)


def evaluate_semantic_status(
    sql: str,
    metric_plan: MetricPlan,
) -> dict:
    """
    Classify existing semantic validator results.

    This is a transitional adapter.
    Unsupported or unknown errors fail closed.
    """

    # Current validator does not support
    # additional user-defined filters.
    if metric_plan.filters:
        return {
            "status": SemanticStatus.UNSUPPORTED.value,
            "reason": (
                "User-defined filters are not yet supported "
                "by the semantic validator."
            ),
        }

    result = validate_metric_semantics(
        sql=sql,
        metric_plan=metric_plan,
    )

    if result["semantic_valid"]:
        return {
            "status": SemanticStatus.VALID.value,
            "reason": None,
        }

    error = result.get("semantic_error") or (
        "Unknown semantic validation failure."
    )

    if any(
        pattern in error
        for pattern in INVALID_ERROR_PATTERNS
    ):
        return {
            "status": SemanticStatus.INVALID.value,
            "reason": error,
        }

    # Unsupported patterns and unclassified errors
    # are never treated as VALID.
    return {
        "status": SemanticStatus.UNSUPPORTED.value,
        "reason": error,
    }
