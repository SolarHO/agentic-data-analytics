
from app.graph.metric_plan import MetricDefinition, MetricPlan
from app.validation.metric_policy import resolve_metric_policies


def test_delay_rate_policy():
    plan = MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name="delay_rate_pct",
                description="Delivery delay percentage",
            )
        ],
        filters=[],
        dimensions=[],
    )

    policies = resolve_metric_policies(plan)

    assert policies["delay_rate_pct"]["required_population"] == [
        "orders.order_status = 'delivered'",
        "orders.order_delivered_customer_date IS NOT NULL",
    ]

    assert policies["delay_rate_pct"]["formula"] == (
        "100 * delayed_orders / "
        "delivered_orders_with_delivery_date"
    )


def test_policy_is_independent_of_llm_description():
    plan = MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name="delayed_orders",
                description="An incorrect model-generated description",
            )
        ],
        filters=[],
        dimensions=[],
    )

    policies = resolve_metric_policies(plan)

    assert (
        "orders.order_status = 'delivered'"
        in policies["delayed_orders"]["required_population"]
    )

    assert policies["delayed_orders"]["calculation_condition"] == (
        "orders.order_delivered_customer_date "
        "> orders.order_estimated_delivery_date"
    )
