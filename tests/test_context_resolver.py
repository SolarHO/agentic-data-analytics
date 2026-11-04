
import pytest

from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)
from app.rag.context_resolver import (
    METRIC_DEPENDENCIES,
    resolve_required_document_ids,
)
from app.context.metric_registry import METRIC_REGISTRY


def make_plan(
    metrics: list[str],
    dimensions: list[str] | None = None,
) -> MetricPlan:
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=name,
                description=name,
            )
            for name in metrics
        ],
        dimensions=dimensions or [],
        filters=[],
    )


def test_product_revenue_required_context():
    plan = make_plan(
        metrics=["product_revenue"],
    )

    result = resolve_required_document_ids(plan)

    assert {
        "metric:product_revenue",
        "business_rule:1",
        "schema:orders",
        "schema:order_items",
        "context:sql_rules",
    } <= result


def test_category_revenue_dependencies():
    plan = make_plan(
        metrics=["product_revenue"],
        dimensions=["category"],
    )

    result = resolve_required_document_ids(plan)

    assert {
        "metric:product_revenue",
        "business_rule:1",
        "dimension:category",
        "business_rule:7",
        "schema:orders",
        "schema:order_items",
        "schema:products",
        "schema:category_translation",
        "context:schema_notes",
    } <= result


def test_monthly_revenue_dependencies():
    plan = make_plan(
        metrics=["product_revenue"],
        dimensions=["month"],
    )

    result = resolve_required_document_ids(plan)

    assert {
        "metric:product_revenue",
        "dimension:month",
        "schema:orders",
        "schema:order_items",
    } <= result


def test_delivery_delay_dependencies():
    plan = make_plan(
        metrics=["delay_rate_pct"],
    )

    result = resolve_required_document_ids(plan)

    assert {
        "metric:delay_rate_pct",
        "business_rule:5",
        "schema:orders",
    } <= result


def test_review_metrics():
    plan = make_plan(
        metrics=["positive_reviews", "negative_reviews"],
    )

    result = resolve_required_document_ids(plan)

    assert {
        "metric:positive_reviews",
        "metric:negative_reviews",
        "business_rule:6",
        "schema:order_reviews",
    } <= result


def test_category_review_join_dependencies():
    plan = make_plan(
        metrics=["avg_review_score"],
        dimensions=["category"],
    )

    result = resolve_required_document_ids(plan)

    assert {
        "schema:order_reviews",
        "schema:orders",
        "schema:order_items",
        "schema:products",
        "schema:category_translation",
    } <= result


def test_all_metrics_have_dependency_mapping():
    assert set(METRIC_REGISTRY) == set(
        METRIC_DEPENDENCIES
    )


def test_unknown_metric_is_rejected():
    plan = make_plan(
        metrics=["product_revenue"],
    )

    # Deliberately bypass Pydantic assignment validation
    # to test the resolver's own fail-closed behavior.
    plan.metrics[0].name = "unknown_metric"

    with pytest.raises(ValueError, match="Unknown metric"):
        resolve_required_document_ids(plan)
