
import pytest

from app.agents.sql_validator import validate_sql


@pytest.mark.parametrize(
    "sql, expected_valid",
    [
        (
            "SELECT COUNT(*) FROM orders",
            True,
        ),
        (
            """
            WITH order_counts AS (
                SELECT customer_id, COUNT(*) AS cnt
                FROM orders
                GROUP BY customer_id
            )
            SELECT AVG(cnt) FROM order_counts
            """,
            True,
        ),
        (
            "SELECT COUNT(*) FROM orders; DELETE FROM orders;",
            False,
        ),
        (
            "DELETE FROM orders",
            False,
        ),
        (
            "SELECT * FROM confidential_table",
            False,
        ),
        (
            "SELECT pg_sleep(1)",
            False,
        ),
        (
            "SELECT FROM orders",
            False,
        ),
        (
            "SELECT * FROM public.orders",
            True,
        ),
        (
            "SELECT * FROM other_schema.orders",
            False,
        ),
        (
            "SELECT pg_catalog.pg_sleep(1)",
            False,
        ),
        (
            "SELECT * FROM pg_catalog.pg_class",
            False,
        ),
        (
            "SELECT SUM(price) FROM order_items",
            True,
        ),
        (
            "SELECT ROUND(AVG(review_score), 2) FROM order_reviews",
            True,
        ),
        (
            """
            SELECT DATE_TRUNC('month', order_purchase_timestamp)
            FROM orders
            """,
            True,
        ),
        (
            "SELECT MIN(price), MAX(price) FROM order_items",
            True,
        ),
        (
            "SELECT current_database()",
            False,
        ),
        (
            "SELECT generate_series(1, 100)",
            False,
        ),
        (
            "SELECT pg_catalog.pg_sleep(1)",
            False,
        ),
        (
            """
            SELECT
                COUNT(
                    CASE
                        WHEN order_status = 'delivered'
                        THEN 1
                    END
                ) AS delivered_orders
            FROM orders
            """,
            True,
        ),
        (
            """
            SELECT
                CASE
                    WHEN COUNT(*) = 0 THEN 0
                    ELSE ROUND(100.0 / COUNT(*), 2)
                END AS rate
            FROM orders
            """,
            True,
        ),
    ],
)
def test_ast_sql_validation(sql, expected_valid):
    result = validate_sql({"sql": sql})

    assert result["sql_valid"] is expected_valid
