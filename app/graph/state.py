from typing import Any, TypedDict


class AnalysisState(TypedDict, total=False):
    question: str
    sql: str
    sql_valid: bool
    validation_error: str | None
    result: list[dict[str, Any]]
    execution_error: str | None