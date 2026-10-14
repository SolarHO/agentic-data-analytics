from typing import Literal

from pydantic import BaseModel, Field

MetricName = Literal[
    "delivered_orders",
    "sold_items",
    "product_revenue",
    "freight_revenue",
    "gross_item_value",
    "average_order_value",
    "delivered_orders_with_delivery_date",
    "delayed_orders",
    "delay_rate_pct",
    "reviews",
    "avg_review_score",
    "negative_reviews",
    "positive_reviews",
]

class MetricDefinition(BaseModel):
    name: MetricName = Field(
        description="Select a canonical metric name from the registry."
    )

    description: str = Field(
        description="Business meaning of the metric."
    )


class MetricPlan(BaseModel):
    #집계, 비교, 추세, 상세 조회
    intent: Literal["aggregation", "comparison", "trend", "detail"]

    #계산할 지표와 그 의미
    metrics: list[MetricDefinition] = Field(
        min_length=1,
        description="Metrics required to answer the user question."
    )

    #분석 대상의 조건
    filters: list[str] = Field(
        default_factory=list,
        description="Business filtering conditions."
    )
    
    #그룹화 기준
    dimensions: list[str] = Field(
        default_factory=list,
        description="Grouping dimensions, such as month or category."
    )