import re

from app.graph.state import AnalysisState


FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
}


def validate_sql(state: AnalysisState) -> AnalysisState:
    sql = state.get("sql", "").strip()

    if not sql:
        return {
            **state,
            "sql_valid": False,
            "validation_error": "SQL is empty.",
        }

    normalized_sql = sql.upper()

    if not (
        normalized_sql.startswith("SELECT")
        or normalized_sql.startswith("WITH")
    ):
        return {
            **state,
            "sql_valid": False,
            "validation_error": "Only SELECT queries are allowed.",
        }

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", normalized_sql):
            return {
                **state,
                "sql_valid": False,
                "validation_error": (
                    f"Forbidden SQL keyword detected: {keyword}"
                ),
            }

    return {
        **state,
        "sql_valid": True,
        "validation_error": None,
    }