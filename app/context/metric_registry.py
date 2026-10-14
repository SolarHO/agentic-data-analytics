METRIC_REGISTRY = {
    "delivered_orders": {
        "description": "Number of distinct delivered orders.",
        "unit": "count",
    },
    "sold_items": {
        "description": "Number of sold order items in delivered orders.",
        "unit": "count",
    },
    "product_revenue": {
        "description": "Sum of item prices for delivered orders, excluding freight.",
        "unit": "currency",
    },
    "freight_revenue": {
        "description": "Sum of freight charges for delivered orders.",
        "unit": "currency",
    },
    "gross_item_value": {
        "description": "Product revenue plus freight revenue for delivered orders.",
        "unit": "currency",
    },
    "average_order_value": {
        "description": "Average order-level product revenue for delivered orders.",
        "unit": "currency",
    },
    "delivered_orders_with_delivery_date": {
        "description": "Number of delivered orders with a non-null actual delivery date.",
        "unit": "count",
    },
    "delayed_orders": {
        "description": "Number of delivered orders delivered after their estimated date.",
        "unit": "count",
    },
    "delay_rate_pct": {
        "description": "Percentage of delivered orders with delivery dates that were delayed.",
        "unit": "percent",
    },
    "reviews": {
        "description": "Total number of reviews.",
        "unit": "count",
    },
    "avg_review_score": {
        "description": "Average review score.",
        "unit": "score",
    },
    "negative_reviews": {
        "description": "Number of reviews with score 1 or 2.",
        "unit": "count",
    },
    "positive_reviews": {
        "description": "Number of reviews with score 4 or 5.",
        "unit": "count",
    },
}