-- ============================================================
-- AI Data Analytics Platform
-- Olist Gold Queries
-- ============================================================


-- ============================================================
-- GQ01. Delivered Sales Summary
-- Definition:
--   product_revenue = SUM(order_items.price)
--   freight_revenue = SUM(order_items.freight_value)
--   gross_item_value = product_revenue + freight_revenue
--   Only delivered orders are included.
-- ============================================================

SELECT
    COUNT(DISTINCT o.order_id) AS delivered_orders,
    COUNT(oi.order_item_id) AS sold_items,
    ROUND(SUM(oi.price), 2) AS product_revenue,
    ROUND(SUM(oi.freight_value), 2) AS freight_revenue,
    ROUND(SUM(oi.price + oi.freight_value), 2) AS gross_item_value
FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered';


-- ============================================================
-- GQ02. Average Order Value (AOV)
-- Definition:
--   Sum product price by order first,
--   then calculate the average across delivered orders.
-- ============================================================

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
SELECT
    ROUND(AVG(order_revenue), 2) AS avg_order_value
FROM order_sales;


-- ============================================================
-- GQ03. Monthly Product Revenue
-- ============================================================

SELECT
    DATE_TRUNC(
        'month',
        o.order_purchase_timestamp
    )::date AS month,

    COUNT(DISTINCT o.order_id) AS orders,

    ROUND(
        SUM(oi.price),
        2
    ) AS product_revenue

FROM orders o
JOIN order_items oi
    ON o.order_id = oi.order_id

WHERE o.order_status = 'delivered'

GROUP BY 1
ORDER BY 1;


-- ============================================================
-- GQ04. Product Revenue by Category
-- LEFT JOIN is intentional because the translation table
-- does not contain every product category.
-- ============================================================

SELECT
    COALESCE(
        ct.product_category_name_english,
        p.product_category_name,
        'unknown'
    ) AS category,

    COUNT(DISTINCT o.order_id) AS orders,

    COUNT(oi.order_item_id) AS sold_items,

    ROUND(
        SUM(oi.price),
        2
    ) AS product_revenue

FROM orders o

JOIN order_items oi
    ON o.order_id = oi.order_id

JOIN products p
    ON oi.product_id = p.product_id

LEFT JOIN category_translation ct
    ON p.product_category_name =
       ct.product_category_name

WHERE o.order_status = 'delivered'

GROUP BY 1
ORDER BY product_revenue DESC;


-- ============================================================
-- GQ05. Delivery Delay Rate
-- Definition:
--   delayed = actual delivery date >
--             estimated delivery date
--   Only delivered orders with an actual delivery timestamp
--   are included.
-- ============================================================

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
  AND order_delivered_customer_date IS NOT NULL;


-- ============================================================
-- GQ06. Review Score Summary
-- ============================================================

SELECT
    COUNT(*) AS reviews,

    ROUND(
        AVG(review_score),
        2
    ) AS avg_review_score,

    COUNT(*) FILTER (
        WHERE review_score <= 2
    ) AS negative_reviews,

    COUNT(*) FILTER (
        WHERE review_score >= 4
    ) AS positive_reviews

FROM order_reviews;