
from app.agents.sql_semantic_validator import (
    validate_sql_semantics,
)
from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)


def make_state(
    metric,
    sql,
    sql_valid=True,
    filters=None,
):
    return {
        "sql": sql,
        "sql_valid": sql_valid,
        "metric_plan": MetricPlan(
            intent="aggregation",
            metrics=[
                MetricDefinition(
                    name=metric,
                    description=metric,
                )
            ],
            filters=filters or [],
            dimensions=[],
        ),
    }


VALID_DELIVERY_SQL = """
SELECT
    COUNT(*) AS delivered_orders_with_delivery_date
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
"""


def test_non_delivery_metric_is_skipped():
    result = validate_sql_semantics(
        make_state(
            "product_revenue",
            "SELECT SUM(price) AS product_revenue FROM order_items",
        )
    )

    assert result["semantic_status"] == "SKIPPED"
    assert result["semantic_error"] is None


def test_valid_delivery_sql():
    result = validate_sql_semantics(
        make_state(
            "delivered_orders_with_delivery_date",
            VALID_DELIVERY_SQL,
        )
    )

    assert result["semantic_status"] == "VALID"


def test_invalid_delivery_sql():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_delivered_customer_date IS NOT NULL
    """

    result = validate_sql_semantics(
        make_state(
            "delivered_orders_with_delivery_date",
            sql,
        )
    )

    assert result["semantic_status"] == "INVALID"
    assert "delivered status missing" in result["semantic_error"]


def test_unsupported_delivery_sql():
    sql = """
    SELECT
        COUNT(DISTINCT order_id)
            AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
    """

    result = validate_sql_semantics(
        make_state(
            "delivered_orders_with_delivery_date",
            sql,
        )
    )

    assert result["semantic_status"] == "UNSUPPORTED"


def test_delivery_sql_with_user_filters_is_unsupported():
    result = validate_sql_semantics(
        make_state(
            "delivered_orders_with_delivery_date",
            VALID_DELIVERY_SQL,
            filters=["order_purchase_timestamp >= '2018-01-01'"],
        )
    )

    assert result["semantic_status"] == "UNSUPPORTED"


def test_ast_validation_failure_is_not_revalidated():
    result = validate_sql_semantics(
        make_state(
            "delivered_orders_with_delivery_date",
            VALID_DELIVERY_SQL,
            sql_valid=False,
        )
    )

    assert result["semantic_status"] == "SKIPPED"
    assert "AST validation" in result["semantic_error"]
