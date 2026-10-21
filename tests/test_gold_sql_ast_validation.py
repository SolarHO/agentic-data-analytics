from pathlib import Path

import pytest
import sqlglot

from app.agents.sql_validator import validate_sql


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_SQL_PATH = PROJECT_ROOT / "sql" / "gold_queries.sql"

GOLD_SQL = GOLD_SQL_PATH.read_text(encoding="utf-8")

GOLD_QUERIES = [
    expression.sql(dialect="postgres")
    for expression in sqlglot.parse(
        GOLD_SQL,
        read="postgres",
        error_level="RAISE",
    )
    if expression is not None
]


def test_gold_query_count():
    assert len(GOLD_QUERIES) == 6


@pytest.mark.parametrize(
    "sql",
    GOLD_QUERIES,
    ids=[f"GQ{i:02d}" for i in range(1, len(GOLD_QUERIES) + 1)],
)
def test_gold_query_passes_ast_validator(sql):
    result = validate_sql({"sql": sql})

    assert result["sql_valid"] is True, (
        f"Gold Query rejected: {result['validation_error']}\n"
        f"SQL:\n{sql}"
    )
