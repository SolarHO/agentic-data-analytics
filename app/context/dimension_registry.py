
DIMENSION_REGISTRY = {
    "month": {
        "description": (
            "Calendar month derived from "
            "orders.order_purchase_timestamp."
        ),
        "expression": (
            "DATE_TRUNC('month', "
            "orders.order_purchase_timestamp)::date"
        ),
        "unit": "month",
    },
    "category": {
        "description": (
            "Product category, using English translation "
            "when available and original category otherwise."
        ),
        "expression": (
            "COALESCE("
            "ct.product_category_name_english, "
            "p.product_category_name, "
            "'unknown')"
        ),
        "unit": "category",
    },
}
