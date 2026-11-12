
from app.graph.analysis_graph import (
    route_after_semantic_validation,
)
from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)


def make_state(metric, status):
    return {
        "sql_valid": True,
        "semantic_status": status,
        "metric_plan": MetricPlan(
            intent="aggregation",
            metrics=[
                MetricDefinition(
                    name=metric,
                    description=metric,
                )
            ],
            filters=[],
            dimensions=[],
        ),
    }


def test_valid_delivery_sql_routes_to_executor():
    state = make_state(
        "delay_rate_pct",
        "VALID",
    )

    assert route_after_semantic_validation(state) == "execute"


def test_invalid_delivery_sql_is_blocked():
    state = make_state(
        "delay_rate_pct",
        "INVALID",
    )

    assert route_after_semantic_validation(state) == "stop"


def test_unsupported_delivery_sql_is_blocked():
    state = make_state(
        "delay_rate_pct",
        "UNSUPPORTED",
    )

    assert route_after_semantic_validation(state) == "stop"


def test_non_delivery_metric_may_skip_semantic_validation():
    state = make_state(
        "product_revenue",
        "SKIPPED",
    )

    assert route_after_semantic_validation(state) == "execute"


def test_delivery_metric_cannot_skip_semantic_validation():
    state = make_state(
        "delay_rate_pct",
        "SKIPPED",
    )

    assert route_after_semantic_validation(state) == "stop"


def test_unknown_status_is_blocked():
    state = make_state(
        "delay_rate_pct",
        "UNKNOWN",
    )

    assert route_after_semantic_validation(state) == "stop"


def test_ast_failure_is_blocked():
    state = make_state(
        "delay_rate_pct",
        "VALID",
    )

    state["sql_valid"] = False

    assert route_after_semantic_validation(state) == "stop"