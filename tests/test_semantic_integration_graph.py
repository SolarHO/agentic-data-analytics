
import pytest

from langgraph.graph import START, END, StateGraph

from app.graph.state import AnalysisState
from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)
from app.graph.analysis_graph import (
    route_after_sql_validation,
    route_after_semantic_validation,
)
from app.agents.sql_validator import validate_sql
from app.agents.sql_semantic_validator import (
    validate_sql_semantics,
)


def make_plan(metric, filters=None):
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=metric,
                description=metric,
            )
        ],
        filters=filters or [],
        dimensions=[],
    )


def build_semantic_test_graph(execution_calls):
    builder = StateGraph(AnalysisState)

    def mock_executor(state):
        execution_calls.append(state["sql"])
        return {
            "result": [{"value": 1}],
            "execution_error": None,
        }

    builder.add_node("sql_validator", validate_sql)

    # Actual semantic validator
    builder.add_node(
        "sql_semantic_validator",
        validate_sql_semantics,
    )

    # Only the database executor is mocked
    builder.add_node("sql_executor", mock_executor)

    builder.add_edge(START, "sql_validator")

    builder.add_conditional_edges(
        "sql_validator",
        route_after_sql_validation,
        {
            "semantic": "sql_semantic_validator",
            "stop": END,
        },
    )

    builder.add_conditional_edges(
        "sql_semantic_validator",
        route_after_semantic_validation,
        {
            "execute": "sql_executor",
            "stop": END,
        },
    )

    builder.add_edge("sql_executor", END)

    return builder.compile()


VALID_SQL = """
SELECT
    COUNT(*) AS delivered_orders_with_delivery_date
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
"""

MISSING_STATUS_SQL = """
SELECT
    COUNT(*) AS delivered_orders_with_delivery_date
FROM orders
WHERE order_delivered_customer_date IS NOT NULL
"""

UNSUPPORTED_COUNT_SQL = """
SELECT
    COUNT(DISTINCT order_id)
        AS delivered_orders_with_delivery_date
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
"""

NON_DELIVERY_SQL = """
SELECT
    SUM(price) AS product_revenue
FROM order_items
"""


@pytest.mark.parametrize(
    "sql, metric, filters, expected_status, should_execute",
    [
        (
            VALID_SQL,
            "delivered_orders_with_delivery_date",
            [],
            "VALID",
            True,
        ),
        (
            MISSING_STATUS_SQL,
            "delivered_orders_with_delivery_date",
            [],
            "INVALID",
            False,
        ),
        (
            UNSUPPORTED_COUNT_SQL,
            "delivered_orders_with_delivery_date",
            [],
            "UNSUPPORTED",
            False,
        ),
        (
            NON_DELIVERY_SQL,
            "product_revenue",
            [],
            "SKIPPED",
            True,
        ),
        (
            VALID_SQL,
            "delivered_orders_with_delivery_date",
            ["order_purchase_timestamp >= '2018-01-01'"],
            "UNSUPPORTED",
            False,
        ),
    ],
)
def test_semantic_execution_routing(
    sql,
    metric,
    filters,
    expected_status,
    should_execute,
):
    execution_calls = []

    graph = build_semantic_test_graph(
        execution_calls,
    )

    result = graph.invoke({
        "sql": sql,
        "metric_plan": make_plan(metric, filters),
    })

    assert result["sql_valid"] is True
    assert result["semantic_status"] == expected_status

    if should_execute:
        assert len(execution_calls) == 1
        assert result["result"] == [{"value": 1}]
    else:
        assert execution_calls == []
        assert not result.get("result")


def test_ast_invalid_sql_never_executes():
    execution_calls = []
    graph = build_semantic_test_graph(execution_calls)

    result = graph.invoke({
        "sql": "DROP TABLE orders",
        "metric_plan": make_plan(
            "delivered_orders_with_delivery_date"
        ),
    })

    assert result["sql_valid"] is False
    assert execution_calls == []
    assert not result.get("result")
