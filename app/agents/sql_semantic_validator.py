
from app.graph.state import AnalysisState
from app.validation.semantic_status import (
    SemanticStatus,
    evaluate_semantic_status,
)


DELIVERY_METRICS = {
    "delivered_orders_with_delivery_date",
    "delayed_orders",
    "delay_rate_pct",
}


def validate_sql_semantics(
    state: AnalysisState,
) -> dict:
    """
    LangGraph adapter for metric-aware semantic validation.

    - Non-delivery metrics: SKIPPED
    - Delivery metrics: VALID / INVALID / UNSUPPORTED
    - Never execute unsupported delivery SQL.
    """

    if not state.get("sql_valid", False):
        return {
            "semantic_status": "SKIPPED",
            "semantic_error": "AST validation has not passed.",
        }

    metric_plan = state.get("metric_plan")
    sql = state.get("sql", "").strip()

    if metric_plan is None:
        return {
            "semantic_status": "UNSUPPORTED",
            "semantic_error": "Metric plan is missing.",
        }

    selected = {
        metric.name
        for metric in metric_plan.metrics
    }

    # Only bypass semantic checking when none of the
    # selected metrics requires delivery-policy validation.
    if not (selected & DELIVERY_METRICS):
        return {
            "semantic_status": "SKIPPED",
            "semantic_error": None,
        }

    if not sql:
        return {
            "semantic_status": "INVALID",
            "semantic_error": "SQL is empty.",
        }

    try:
        result = evaluate_semantic_status(
            sql=sql,
            metric_plan=metric_plan,
        )

        return {
            "semantic_status": result["status"],
            "semantic_error": result["reason"],
        }

    except Exception as exc:
        # Fail closed. Do not approve SQL when semantic
        # validation unexpectedly fails.
        return {
            "semantic_status": SemanticStatus.UNSUPPORTED.value,
            "semantic_error": (
                f"Semantic validation error: "
                f"{type(exc).__name__}: {exc}"
            ),
        }
