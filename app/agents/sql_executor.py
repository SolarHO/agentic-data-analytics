
from sqlalchemy import text

from app.agents.sql_error_classifier import classify_sql_error
from app.db.postgres import read_engine
from app.graph.state import AnalysisState

#최대 결과행 수 제한
MAX_RESULT_ROWS = 1000

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

            # rows = [
            #     dict(row)
            #     for row in query_result.mappings().all()
            # ]
            fetched_rows = query_result.mappings().fetchmany(
                MAX_RESULT_ROWS + 1
            )

            if len(fetched_rows) > MAX_RESULT_ROWS:
                return {
                    "result": [],
                    "execution_error": (
                        f"Query result exceeds the maximum "
                        f"of {MAX_RESULT_ROWS} rows."
                    ),
                    "execution_error_type": "result_limit_exceeded",
                }

            rows = [dict(row) for row in fetched_rows]

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
