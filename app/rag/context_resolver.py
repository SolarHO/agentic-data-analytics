
from dataclasses import dataclass

from app.graph.metric_plan import MetricPlan
from app.context.metric_registry import METRIC_REGISTRY
from app.context.dimension_registry import DIMENSION_REGISTRY


@dataclass(frozen=True)
class ContextDependency:
    tables: tuple[str, ...]
    rules: tuple[int, ...] = ()


# Metric별 필수 테이블과 비즈니스 규칙
METRIC_DEPENDENCIES = {
    "delivered_orders": ContextDependency(
        tables=("orders",),
    ),
    "sold_items": ContextDependency(
        tables=("orders", "order_items"),
        rules=(1,),
    ),
    "product_revenue": ContextDependency(
        tables=("orders", "order_items"),
        rules=(1,),
    ),
    "freight_revenue": ContextDependency(
        tables=("orders", "order_items"),
        rules=(2,),
    ),
    "gross_item_value": ContextDependency(
        tables=("orders", "order_items"),
        rules=(3,),
    ),
    "average_order_value": ContextDependency(
        tables=("orders", "order_items"),
        rules=(4,),
    ),
    "delivered_orders_with_delivery_date": ContextDependency(
        tables=("orders",),
        rules=(5,),
    ),
    "delayed_orders": ContextDependency(
        tables=("orders",),
        rules=(5,),
    ),
    "delay_rate_pct": ContextDependency(
        tables=("orders",),
        rules=(5,),
    ),
    "reviews": ContextDependency(
        tables=("order_reviews",),
        rules=(6,),
    ),
    "avg_review_score": ContextDependency(
        tables=("order_reviews",),
        rules=(6,),
    ),
    "negative_reviews": ContextDependency(
        tables=("order_reviews",),
        rules=(6,),
    ),
    "positive_reviews": ContextDependency(
        tables=("order_reviews",),
        rules=(6,),
    ),
}


# Dimension별 필수 테이블과 비즈니스 규칙
DIMENSION_DEPENDENCIES = {
    "month": ContextDependency(
        tables=("orders",),
    ),
    "category": ContextDependency(
        tables=("products", "category_translation"),
        rules=(7,),
    ),
}


def resolve_required_document_ids(
    metric_plan: MetricPlan,
) -> set[str]:
    """
    Resolve required RAG document IDs from a MetricPlan.

    No LLM or vector search is performed.
    """

    required_ids = {"context:sql_rules"}

    # 1. Metric dependencies
    for metric in metric_plan.metrics:
        metric_name = metric.name

        if metric_name not in METRIC_REGISTRY:
            raise ValueError(
                f"Unknown metric: {metric_name}"
            )

        dependency = METRIC_DEPENDENCIES.get(metric_name)

        if dependency is None:
            raise ValueError(
                f"No dependency mapping for metric: {metric_name}"
            )

        required_ids.add(f"metric:{metric_name}")

        required_ids.update(
            f"schema:{table}"
            for table in dependency.tables
        )

        required_ids.update(
            f"business_rule:{rule}"
            for rule in dependency.rules
        )

    # 2. Dimension dependencies
    for dimension in metric_plan.dimensions:
        if dimension not in DIMENSION_REGISTRY:
            raise ValueError(
                f"Unknown dimension: {dimension}"
            )

        dependency = DIMENSION_DEPENDENCIES.get(dimension)

        if dependency is None:
            raise ValueError(
                f"No dependency mapping for dimension: {dimension}"
            )

        required_ids.add(f"dimension:{dimension}")

        required_ids.update(
            f"schema:{table}"
            for table in dependency.tables
        )

        required_ids.update(
            f"business_rule:{rule}"
            for rule in dependency.rules
        )

    # 3. Join dependencies
    # Category analysis of order/review metrics
    # requires additional relationship tables.
    if "category" in metric_plan.dimensions:
        required_ids.add("schema:order_items")

        if any(
            metric.name in {
                "reviews",
                "avg_review_score",
                "negative_reviews",
                "positive_reviews",
            }
            for metric in metric_plan.metrics
        ):
            required_ids.add("schema:orders")

    if "month" in metric_plan.dimensions:
        if any(
            metric.name in {
                "reviews",
                "avg_review_score",
                "negative_reviews",
                "positive_reviews",
            }
            for metric in metric_plan.metrics
        ):
            required_ids.add("schema:orders")

    # 4. Schema notes for category analysis
    if "category" in metric_plan.dimensions:
        required_ids.add("context:schema_notes")

    return required_ids
