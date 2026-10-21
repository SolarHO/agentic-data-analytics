
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.graph.state import AnalysisState


ALLOWED_TABLES = {
    "customers",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "sellers",
    "category_translation",
    "geolocation",
}

ALLOWED_FUNCTIONS = {
    "count",
    "sum",
    "avg",
    "coalesce",
    "timestamp_trunc",
    "round",
    "min",
    "max",
    "cast",
}


def validate_sql(state: AnalysisState) -> dict:
    sql = state.get("sql", "").strip()

    if not sql:
        return {
            "sql_valid": False,
            "validation_error": "SQL is empty.",
        }

    try:
        statements = [
            statement
            for statement in sqlglot.parse(
                sql,
                read="postgres",
                error_level="RAISE",
            )
            if statement is not None
        ]

        if len(statements) != 1:
            return {
                "sql_valid": False,
                "validation_error": (
                    "Exactly one SQL statement is allowed."
                ),
            }

        expression = statements[0]

        if not isinstance(expression, exp.Select):
            return {
                "sql_valid": False,
                "validation_error": (
                    "Only SELECT queries are allowed."
                ),
            }
        
        # Every SELECT, including SELECTs inside CTEs, must project a value.
        for select_node in expression.find_all(exp.Select):
            if not select_node.expressions:
                return {
                    "sql_valid": False,
                    "validation_error": (
                        "SELECT must contain at least one expression."
                    ),
                }

        # Block write operations anywhere in the AST.
        blocked_nodes = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Create,
            exp.Alter,
            exp.TruncateTable,
            exp.Command,
        )

        for node in expression.walk():
            if isinstance(node, blocked_nodes):
                return {
                    "sql_valid": False,
                    "validation_error": (
                        "Write or administrative SQL is prohibited."
                    ),
                }

        # CTE names are not physical database tables.
        cte_names = {
            cte.alias_or_name.lower()
            for cte in expression.find_all(exp.CTE)
        }

        ALLOWED_SCHEMAS = {"", "public"}

        for table in expression.find_all(exp.Table):
            table_name = table.name.lower()
            schema_name = table.db.lower() if table.db else ""

            # 명시적으로 허용되지 않은 스키마 차단
            if schema_name not in ALLOWED_SCHEMAS:
                return {
                    "sql_valid": False,
                    "validation_error": (
                        f"Schema '{schema_name}' is not allowed."
                    ),
                }

            # CTE 이름은 실제 DB 테이블이 아님
            if not schema_name and table_name in cte_names:
                continue

            if table_name not in ALLOWED_TABLES:
                return {
                    "sql_valid": False,
                    "validation_error": (
                        f"Table '{table_name}' is not allowed."
                    ),
                }

        for function in expression.find_all(exp.Func):

            # SQL expressions/operators, not external function calls.
            if isinstance(
                function,
                (
                    exp.And,
                    exp.Or,
                    exp.Not,
                    exp.Case,
                    exp.If,
                ),
            ):
                continue

            if isinstance(function, exp.Anonymous):
                function_name = function.name.lower()
            else:
                function_name = function.sql_name().lower()

            if function_name not in ALLOWED_FUNCTIONS:
                return {
                    "sql_valid": False,
                    "validation_error": (
                        f"Function '{function_name}' is not allowed."
                    ),
                }

        return {
            "sql_valid": True,
            "validation_error": None,
        }

    except (ParseError, sqlglot.errors.TokenError) as exc:
        return {
            "sql_valid": False,
            "validation_error": f"SQL parsing failed: {exc}",
        }
