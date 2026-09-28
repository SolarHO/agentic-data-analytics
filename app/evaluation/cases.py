from decimal import Decimal
from typing import Any, TypedDict


class ExpectedMetric(TypedDict):
    value: Any
    aliases: list[str]


class EvaluationCase(TypedDict):
    id: str
    question: str
    expected: dict[str, ExpectedMetric]


EVALUATION_CASES: list[EvaluationCase] = [
    {
        "id": "GQ01",
        "question": (
            "배송 완료된 주문의 총 주문 수, 판매 상품 수, "
            "상품 매출, 배송비 매출, 총 거래 금액을 알려줘."
        ),
        "expected": {
            "delivered_orders": {
                "value": 96478,
                "aliases": [
                    "delivered_orders",
                    "total_orders",
                    "total_delivered_orders",
                ],
            },
            "sold_items": {
                "value": 110197,
                "aliases": [
                    "sold_items",
                    "total_items_sold",
                ],
            },
            "product_revenue": {
                "value": Decimal("13221498.11"),
                "aliases": [
                    "product_revenue",
                ],
            },
            "freight_revenue": {
                "value": Decimal("2198275.64"),
                "aliases": [
                    "freight_revenue",
                ],
            },
            "gross_item_value": {
                "value": Decimal("15419773.75"),
                "aliases": [
                    "gross_item_value",
                    "total_gross_value",
                    "gross_transaction_value",
                ],
            },
        },
    },
    {
        "id": "GQ02",
        "question": "평균 주문 금액은 얼마야?",
        "expected": {
            "average_order_value": {
                "value": Decimal("137.04"),
                "aliases": [
                    "average_order_value",
                    "aov",
                ],
            },
        },
    },
    {
        "id": "GQ05",
        "question": (
            "배송 완료된 주문 중 배송일 정보가 있는 주문 수, "
            "배송 지연 주문 수, 배송 지연율을 알려줘."
        ),
        "expected": {
            "delivered_orders": {
                "value": 96470,
                "aliases": [
                    "delivered_orders",
                    "total_orders",
                    "total_delivered_orders",
                    "orders_with_delivery_info",
                    "delivered_with_delivery_date",
                ],
            },
            "delayed_orders": {
                "value": 7826,
                "aliases": [
                    "delayed_orders",
                    "late_orders",
                ],
            },
            "delay_rate_pct": {
                "value": Decimal("8.11"),
                "aliases": [
                    "delay_rate_pct",
                    "delivery_delay_rate_percent",
                    "delay_rate",
                ],
            },
        },
    },
    {
        "id": "GQ06",
        "question": (
            "전체 리뷰 수, 평균 리뷰 점수, "
            "부정 리뷰 수와 긍정 리뷰 수를 알려줘."
        ),
        "expected": {
            "reviews": {
                "value": 99224,
                "aliases": [
                    "reviews",
                    "total_reviews",
                ],
            },
            "avg_review_score": {
                "value": Decimal("4.09"),
                "aliases": [
                    "avg_review_score",
                    "average_review_score",
                ],
            },
            "negative_reviews": {
                "value": 14575,
                "aliases": [
                    "negative_reviews",
                ],
            },
            "positive_reviews": {
                "value": 76470,
                "aliases": [
                    "positive_reviews",
                ],
            },
        },
    },
]