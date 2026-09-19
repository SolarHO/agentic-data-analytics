from decimal import Decimal

from sqlalchemy import text

from app.db.postgres import engine


def test_delivered_sales_summary():
    sql = text("""
        SELECT
            COUNT(DISTINCT o.order_id) AS delivered_orders,
            COUNT(oi.order_item_id) AS sold_items,
            ROUND(SUM(oi.price), 2) AS product_revenue,
            ROUND(SUM(oi.freight_value), 2) AS freight_revenue,
            ROUND(SUM(oi.price + oi.freight_value), 2) AS gross_item_value
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
    """)

    with engine.connect() as connection:
        result = connection.execute(sql).mappings().one()

    assert result["delivered_orders"] == 96478
    assert result["sold_items"] == 110197
    assert result["product_revenue"] == Decimal("13221498.11")
    assert result["freight_revenue"] == Decimal("2198275.64")
    assert result["gross_item_value"] == Decimal("15419773.75")


def test_average_order_value():
    sql = text("""
        WITH order_sales AS (
            SELECT
                o.order_id,
                SUM(oi.price) AS order_revenue
            FROM orders o
            JOIN order_items oi
                ON o.order_id = oi.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY o.order_id
        )
        SELECT ROUND(AVG(order_revenue), 2) AS avg_order_value
        FROM order_sales
    """)

    with engine.connect() as connection:
        result = connection.execute(sql).scalar_one()

    assert result == Decimal("137.04")


def test_delivery_delay_rate():
    sql = text("""
        SELECT
            COUNT(*) AS delivered_orders,
            COUNT(*) FILTER (
                WHERE order_delivered_customer_date >
                      order_estimated_delivery_date
            ) AS delayed_orders,
            ROUND(
                100.0 *
                COUNT(*) FILTER (
                    WHERE order_delivered_customer_date >
                          order_estimated_delivery_date
                )
                / COUNT(*),
                2
            ) AS delay_rate_pct
        FROM orders
        WHERE order_status = 'delivered'
          AND order_delivered_customer_date IS NOT NULL
    """)

    with engine.connect() as connection:
        result = connection.execute(sql).mappings().one()

    assert result["delivered_orders"] == 96470
    assert result["delayed_orders"] == 7826
    assert result["delay_rate_pct"] == Decimal("8.11")


def test_review_summary():
    sql = text("""
        SELECT
            COUNT(*) AS reviews,
            ROUND(AVG(review_score), 2) AS avg_review_score,
            COUNT(*) FILTER (
                WHERE review_score <= 2
            ) AS negative_reviews,
            COUNT(*) FILTER (
                WHERE review_score >= 4
            ) AS positive_reviews
        FROM order_reviews
    """)

    with engine.connect() as connection:
        result = connection.execute(sql).mappings().one()

    assert result["reviews"] == 99224
    assert result["avg_review_score"] == Decimal("4.09")
    assert result["negative_reviews"] == 14575
    assert result["positive_reviews"] == 76470
