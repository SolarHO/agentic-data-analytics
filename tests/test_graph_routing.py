from app.graph.analysis_graph import (
    route_after_sql_validation,
)

from langgraph.graph import END, START, StateGraph

from app.agents.sql_validator import validate_sql
from app.graph.analysis_graph import route_after_sql_validation, route_after_sql_execution
from app.graph.state import AnalysisState


def test_valid_sql_routes_to_executor():
    state = {
        "sql": "SELECT COUNT(*) FROM orders",
        "sql_valid": True,
    }

    route = route_after_sql_validation(state)

    assert route == "execute"


def test_invalid_sql_routes_to_end():
    state = {
        "sql": "DROP TABLE orders",
        "sql_valid": False,
    }

    route = route_after_sql_validation(state)

    assert route == "stop"


def test_missing_validation_result_routes_to_end():
    state = {
        "sql": "SELECT * FROM orders",
    }

    route = route_after_sql_validation(state)

    assert route == "stop"


def build_test_graph(executor):
    """Build a graph using the real validator and a mock executor."""

    builder = StateGraph(AnalysisState)

    builder.add_node("sql_validator", validate_sql)
    builder.add_node("sql_executor", executor)

    builder.add_edge(START, "sql_validator")

    builder.add_conditional_edges(
        "sql_validator",
        route_after_sql_validation,
        {
            "execute": "sql_executor",
            "stop": END,
        },
    )

    builder.add_edge("sql_executor", END)

    return builder.compile()


def test_invalid_sql_skips_executor():
    calls = []

    def mock_executor(state: AnalysisState):
        calls.append("executed")
        return {"result": [{"value": 1}]}

    graph = build_test_graph(mock_executor)

    result = graph.invoke({
        "sql": "DROP TABLE orders",
    })

    assert result["sql_valid"] is False
    assert calls == []
    assert "result" not in result


def test_valid_sql_calls_executor():
    calls = []

    def mock_executor(state: AnalysisState):
        calls.append("executed")
        return {"result": [{"value": 1}]}

    graph = build_test_graph(mock_executor)

    result = graph.invoke({
        "sql": "SELECT COUNT(*) FROM orders",
    })

    assert result["sql_valid"] is True
    assert calls == ["executed"]
    assert result["result"] == [{"value": 1}]

def test_execution_success_routes_to_contract():
    state = {
        "execution_error": None,
        "retry_count": 0,
    }

    assert route_after_sql_execution(state) == "success"


def test_undefined_column_routes_to_retry():
    state = {
        "execution_error": "column does not exist",
        "execution_error_type": "undefined_column",
        "retry_count": 0,
    }

    assert route_after_sql_execution(state) == "retry"


def test_permission_denied_routes_to_stop():
    state = {
        "execution_error": "permission denied",
        "execution_error_type": "permission_denied",
        "retry_count": 0,
    }

    assert route_after_sql_execution(state) == "stop"


def test_retry_limit_routes_to_stop():
    state = {
        "execution_error": "column does not exist",
        "execution_error_type": "undefined_column",
        "retry_count": 1,
    }

    assert route_after_sql_execution(state) == "stop"


def test_unknown_error_routes_to_stop():
    state = {
        "execution_error": "unexpected error",
        "execution_error_type": "unknown",
        "retry_count": 0,
    }

    assert route_after_sql_execution(state) == "stop"