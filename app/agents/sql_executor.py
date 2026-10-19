
from sqlalchemy import text

from app.agents.sql_error_classifier import (
    classify_sql_error,
)
from app.db.postgres import read_engine
from app.graph.state import AnalysisState


def execute_sql(state: AnalysisState) -> AnalysisState:
    if not state.get("sql_valid", False):
        return {
            "result": [],
            "execution_error": "SQL validation failed.",
            "execution_error_type": "validation_error",
        }

    sql = state.get("sql", "").strip()

    try:
        with read_engine.connect() as connection:
            query_result = connection.execute(text(sql))

            rows = [
                dict(row)
                for row in query_result.mappings().all()
            ]

        return {
            "result": rows,
            "execution_error": None,
            "execution_error_type": None,
        }

    except Exception as exc:
        error_type = classify_sql_error(exc)

        return {
            "result": [],
            "execution_error": str(exc),
            "execution_error_type": error_type.value,
        }
