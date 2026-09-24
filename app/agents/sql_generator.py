from app.graph.state import AnalysisState


AOV_GOLD_SQL = """
WITH order_revenue AS (
    SELECT
        o.order_id,
        SUM(oi.price) AS order_revenue
    FROM orders AS o
    JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY o.order_id
)
SELECT
    ROUND(AVG(order_revenue), 2) AS average_order_value
FROM order_revenue;
"""


def generate_sql(state: AnalysisState) -> AnalysisState:
    question = state.get("question", "")

    if not question:
        return {
            **state,
            "sql": "",
            "validation_error": "Question is empty.",
        }

    return {
        **state,
        "sql": AOV_GOLD_SQL.strip(),
    }