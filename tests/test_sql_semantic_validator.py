
from app.graph.metric_plan import MetricDefinition, MetricPlan
from app.validation.sql_semantic_validator import (
    validate_metric_semantics,
)


def make_plan(*names):
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=name,
                description=name,
            )
            for name in names
        ],
        filters=[],
        dimensions=[],
    )


def test_valid_where_population():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is True


def test_missing_status_rejected():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_delivered_customer_date IS NOT NULL
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False
    assert "delivered status missing" in result["semantic_error"]


def test_missing_date_check_rejected():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False


def test_valid_count_filter():
    sql = """
    SELECT
        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date IS NOT NULL
        ) AS delivered_orders_with_delivery_date
    FROM orders
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is True


def test_delayed_orders_condition_required():
    sql = """
    SELECT
        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date IS NOT NULL
        ) AS delayed_orders
    FROM orders
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delayed_orders"),
    )

    assert result["semantic_valid"] is False
    assert "delay comparison missing" in result["semantic_error"]


def test_delayed_orders_valid():
    sql = """
    SELECT
        COUNT(*) FILTER (
            WHERE order_status = 'delivered'
              AND order_delivered_customer_date IS NOT NULL
              AND order_delivered_customer_date >
                  order_estimated_delivery_date
        ) AS delayed_orders
    FROM orders
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delayed_orders"),
    )

    assert result["semantic_valid"] is True


def test_or_condition_cannot_satisfy_policy():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
       OR order_delivered_customer_date IS NOT NULL
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False


def test_rate_metric_not_yet_supported():
    sql = """
    SELECT 8.11 AS delay_rate_pct
    FROM orders
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delay_rate_pct"),
    )

    assert result["semantic_valid"] is False
    assert "Unsupported metrics" in result["semantic_error"]


def test_qualified_null_check():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders AS o
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is True


def test_gq05_missing_population_in_cte_rejected():
    sql = """
    WITH stats AS (
        SELECT
            COUNT(*) FILTER (
                WHERE order_delivered_customer_date IS NOT NULL
            ) AS delivered_orders_with_delivery_date,

            COUNT(*) FILTER (
                WHERE order_delivered_customer_date IS NOT NULL
                  AND order_delivered_customer_date >
                      order_estimated_delivery_date
            ) AS delayed_orders

        FROM orders
    )
    SELECT
        delivered_orders_with_delivery_date,
        delayed_orders,

        ROUND(
            CASE
                WHEN delivered_orders_with_delivery_date = 0
                THEN 0
                ELSE (
                    delayed_orders::numeric /
                    delivered_orders_with_delivery_date::numeric
                ) * 100
            END,
            2
        ) AS delay_rate_pct

    FROM stats
    """

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
            "delay_rate_pct",
        ),
    )

    assert result["semantic_valid"] is False


def test_gq05_valid_cte_passes():
    sql = """
    WITH stats AS (
        SELECT
            COUNT(*) AS delivered_orders_with_delivery_date,

            COUNT(*) FILTER (
                WHERE order_delivered_customer_date >
                      order_estimated_delivery_date
            ) AS delayed_orders

        FROM orders

        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
    )

    SELECT
        delivered_orders_with_delivery_date,
        delayed_orders,

        ROUND(
            CASE
                WHEN delivered_orders_with_delivery_date = 0
                THEN 0
                ELSE
                    100.0 * delayed_orders
                    / delivered_orders_with_delivery_date
            END,
            2
        ) AS delay_rate_pct

    FROM stats
    """

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
            "delay_rate_pct",
        ),
    )

    assert result["semantic_valid"] is True, result["semantic_error"]

def test_valid_cte_count_metrics():
    sql = """
    WITH stats AS (
        SELECT
            COUNT(*) AS delivered_orders_with_delivery_date,

            COUNT(*) FILTER (
                WHERE order_delivered_customer_date >
                      order_estimated_delivery_date
            ) AS delayed_orders

        FROM orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
    )
    SELECT
        delivered_orders_with_delivery_date,
        delayed_orders
    FROM stats
    """

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
        ),
    )

    assert result["semantic_valid"] is True, result["semantic_error"]


def test_cte_missing_status_is_rejected():
    sql = """
    WITH stats AS (
        SELECT
            COUNT(*) AS delivered_orders_with_delivery_date,

            COUNT(*) FILTER (
                WHERE order_delivered_customer_date >
                      order_estimated_delivery_date
            ) AS delayed_orders

        FROM orders
        WHERE order_delivered_customer_date IS NOT NULL
    )
    SELECT
        delivered_orders_with_delivery_date,
        delayed_orders
    FROM stats
    """

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
        ),
    )

    assert result["semantic_valid"] is False
    assert "delivered status missing" in result["semantic_error"]


def make_gq05_cte_sql(formula):
    return f"""
    WITH stats AS (
        SELECT
            COUNT(*) AS delivered_orders_with_delivery_date,

            COUNT(*) FILTER (
                WHERE order_delivered_customer_date >
                      order_estimated_delivery_date
            ) AS delayed_orders

        FROM orders

        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
    )
    SELECT
        delivered_orders_with_delivery_date
            AS delivered_orders_with_delivery_date,
        delayed_orders AS delayed_orders,
        {formula} AS delay_rate_pct
    FROM stats
    """


def test_gq05_cte_invalid_rate_formula():
    sql = make_gq05_cte_sql("""
        ROUND(
            CASE
                WHEN delivered_orders_with_delivery_date = 0
                THEN 0
                ELSE
                    100.0 * delivered_orders_with_delivery_date
                    / delayed_orders
            END,
            2
        )
    """)

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
            "delay_rate_pct",
        ),
    )

    assert result["semantic_valid"] is False
    assert "invalid calculation formula" in result["semantic_error"]


def test_gq05_cte_valid_rate_formula():
    sql = make_gq05_cte_sql("""
        ROUND(
            CASE
                WHEN delivered_orders_with_delivery_date = 0
                THEN 0
                ELSE
                    100.0 * delayed_orders
                    / delivered_orders_with_delivery_date
            END,
            2
        )
    """)

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
            "delay_rate_pct",
        ),
    )

    assert result["semantic_valid"] is True, result["semantic_error"]

def test_gq05_cte_without_rate_alias_rejected():
    sql = make_gq05_cte_sql("""
        ROUND(
            CASE
                WHEN delivered_orders_with_delivery_date = 0
                THEN 0
                ELSE
                    100.0 * delayed_orders
                    / delivered_orders_with_delivery_date
            END,
            2
        )
    """)

    sql = sql.replace(
        "AS delay_rate_pct\n    FROM stats",
        "FROM stats",
    )

    result = validate_metric_semantics(
        sql,
        make_plan(
            "delivered_orders_with_delivery_date",
            "delayed_orders",
            "delay_rate_pct",
        ),
    )

    assert result["semantic_valid"] is False



def test_extra_global_filter_rejected():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_purchase_timestamp >= '2018-01-01'
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False


def test_denominator_with_delay_filter_rejected():
    sql = """
    SELECT
        COUNT(*) AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_delivered_customer_date >
          order_estimated_delivery_date
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False


def test_distinct_count_is_not_supported():
    sql = """
    SELECT
        COUNT(DISTINCT order_id)
            AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False


def test_count_column_is_not_supported():
    sql = """
    SELECT
        COUNT(order_id)
            AS delivered_orders_with_delivery_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
    """

    result = validate_metric_semantics(
        sql,
        make_plan("delivered_orders_with_delivery_date"),
    )

    assert result["semantic_valid"] is False
    assert "Unsupported aggregate" in result["semantic_error"]