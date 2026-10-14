from typing import Any, TypedDict

from app.graph.metric_plan import MetricPlan


class AnalysisState(TypedDict, total=False):
    question: str

    metric_plan: MetricPlan

    sql: str
    sql_valid: bool
    validation_error: str | None

    result: list[dict[str, Any]]
    execution_error: str | None

    contract_valid: bool
    contract_error: str | None