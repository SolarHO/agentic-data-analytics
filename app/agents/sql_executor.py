from sqlalchemy import text

from app.db.postgres import engine
from app.graph.state import AnalysisState


def execute_sql(state: AnalysisState) -> AnalysisState:
    if not state.get("sql_valid", False):
        return {
            **state,
            "result": [],
            "execution_error": "SQL validation failed.",
        }

    sql = state.get("sql", "").strip()

    try:
        with engine.connect() as connection:
            query_result = connection.execute(text(sql))

            rows = [
                dict(row)
                for row in query_result.mappings().all()
            ]

        return {
            **state,
            "result": rows,
            "execution_error": None,
        }

    except Exception as exc:
        return {
            **state,
            "result": [],
            "execution_error": str(exc),
        }