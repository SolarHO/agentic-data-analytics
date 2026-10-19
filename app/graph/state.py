from typing import Any, TypedDict, NotRequired

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

    execution_error_type: str | None
    retry_count: int
    # retry_count = 0: 최초 생성 SQL 실행
    # retry_count = 1: SQL 재생성 1회 수행
    # retry_count >= 1: 추가 재생성 금지

    sql_recovery_history: list[dict]
    recovery_status: NotRequired[str]