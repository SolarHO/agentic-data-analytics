
from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)
from app.validation.semantic_status import (
    evaluate_semantic_status,
)


def make_plan(name, filters=None):
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=name,
                description=name,
            )
        ],
        filters=filters or [],
        dimensions=[],
    )


VALID_SQL = """
SELECT
    COUNT(*) AS delivered_orders_with_delivery_date
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
"""


def test_valid_sql_status():
    result = evaluate_semantic_status(
        VALID_SQL,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["status"] == "VALID"
    assert result["reason"] is None


def test_missing_population_is_invalid():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_delivered_customer_date IS NOT NULL
    """

    result = evaluate_semantic_status(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["status"] == "INVALID"
    assert "delivered status missing" in result["reason"]


def test_unsupported_metric_structure():
    sql = """
    SELECT 8.11 AS delay_rate_pct
    FROM orders
    """

    result = evaluate_semantic_status(
        sql,
        make_plan("delay_rate_pct"),
    )

    assert result["status"] == "UNSUPPORTED"


def test_unsupported_count_expression():
    sql = """
    SELECT
        COUNT(DISTINCT order_id)
            AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
    """

    result = evaluate_semantic_status(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["status"] == "UNSUPPORTED"


def test_user_filters_are_unsupported():
    result = evaluate_semantic_status(
        VALID_SQL,
        make_plan(
            "delivered_orders_with_delivery_date",
            filters=[
                "order_purchase_timestamp >= '2018-01-01'"
            ],
        ),
    )

    assert result["status"] == "UNSUPPORTED"
