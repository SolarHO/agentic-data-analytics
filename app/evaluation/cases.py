
from decimal import Decimal
from typing import Any, TypedDict


class EvaluationCase(TypedDict):
    id: str
    question: str
    expected: dict[str, Any]


EVALUATION_CASES: list[EvaluationCase] = [
    {
        "id": "GQ01",
        "question": (
            "배송 완료된 주문의 총 주문 수, 판매 상품 수, "
            "상품 매출, 배송비 매출, 총 거래 금액을 알려줘."
        ),
        "expected": {
            "delivered_orders": 96478,
            "sold_items": 110197,
            "product_revenue": Decimal("13221498.11"),
            "freight_revenue": Decimal("2198275.64"),
            "gross_item_value": Decimal("15419773.75"),
        },
    },
    {
        "id": "GQ02",
        "question": "평균 주문 금액은 얼마야?",
        "expected": {
            "average_order_value": Decimal("137.04"),
        },
    },
    {
        "id": "GQ05",
        "question": (
            "배송 완료된 주문 중 배송일 정보가 있는 주문 수, "
            "배송 지연 주문 수, 배송 지연율을 알려줘."
        ),
        "expected": {
            "delivered_orders_with_delivery_date": 96470,
            "delayed_orders": 7826,
            "delay_rate_pct": Decimal("8.11"),
        },
    },
    {
        "id": "GQ06",
        "question": (
            "전체 리뷰 수, 평균 리뷰 점수, "
            "부정 리뷰 수와 긍정 리뷰 수를 알려줘."
        ),
        "expected": {
            "reviews": 99224,
            "avg_review_score": Decimal("4.09"),
            "negative_reviews": 14575,
            "positive_reviews": 76470,
        },
    },
]
