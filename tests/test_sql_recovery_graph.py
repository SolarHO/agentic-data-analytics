
from langgraph.graph import END, START, StateGraph

from app.graph.state import AnalysisState
from app.graph.analysis_graph import (
    route_after_sql_validation,
    route_after_sql_execution,
)
from app.agents.sql_validator import validate_sql


def build_recovery_test_graph(executor, repair, contract):
    builder = StateGraph(AnalysisState)

    builder.add_node("sql_validator", validate_sql)
    builder.add_node("sql_executor", executor)
    builder.add_node("sql_repair", repair)
    builder.add_node("output_contract_validator", contract)

    builder.add_edge(START, "sql_validator")

    builder.add_conditional_edges(
        "sql_validator",
        route_after_sql_validation,
        {
            "execute": "sql_executor",
            "stop": END,
        },
    )

    builder.add_conditional_edges(
        "sql_executor",
        route_after_sql_execution,
        {
            "success": "output_contract_validator",
            "retry": "sql_repair",
            "stop": END,
        },
    )

    builder.add_edge("sql_repair", "sql_validator")
    builder.add_edge("output_contract_validator", END)

    return builder.compile()


def test_recoverable_error_repairs_once():
    calls = []

    def mock_executor(state):
        calls.append("execute")

        if state.get("retry_count", 0) == 0:
            return {
                "execution_error": "column does not exist",
                "execution_error_type": "undefined_column",
                "result": [],
            }

        return {
            "execution_error": None,
            "execution_error_type": None,
            "result": [{"total_orders": 99441}],
        }

    def mock_repair(state):
        calls.append("repair")
        return {
            "sql": "SELECT COUNT(*) AS total_orders FROM orders",
            "sql_valid": False,
            "retry_count": state.get("retry_count", 0) + 1,
            "execution_error": None,
            "execution_error_type": None,
        }

    def mock_contract(state):
        calls.append("contract")
        return {"contract_valid": True}

    graph = build_recovery_test_graph(
        mock_executor,
        mock_repair,
        mock_contract,
    )

    result = graph.invoke({
        "sql": "SELECT nonexistent_column FROM orders",
        "retry_count": 0,
    })

    assert calls == [
        "execute",
        "repair",
        "execute",
        "contract",
    ]
    assert result["retry_count"] == 1
    assert result["execution_error"] is None
    assert result["contract_valid"] is True


def test_permission_error_stops_without_repair():
    calls = []

    def mock_executor(state):
        calls.append("execute")
        return {
            "execution_error": "permission denied",
            "execution_error_type": "permission_denied",
            "result": [],
        }

    def mock_repair(state):
        calls.append("repair")
        return {"retry_count": 1}

    def mock_contract(state):
        calls.append("contract")
        return {"contract_valid": True}

    graph = build_recovery_test_graph(
        mock_executor,
        mock_repair,
        mock_contract,
    )

    result = graph.invoke({
        "sql": "SELECT COUNT(*) FROM orders",
        "retry_count": 0,
    })

    assert calls == ["execute"]
    assert result["execution_error_type"] == "permission_denied"
    assert result["retry_count"] == 0


def test_second_execution_error_stops():
    calls = []

    def mock_executor(state):
        calls.append("execute")
        return {
            "execution_error": "column does not exist",
            "execution_error_type": "undefined_column",
            "result": [],
        }

    def mock_repair(state):
        calls.append("repair")
        return {
            "sql": "SELECT another_column FROM orders",
            "sql_valid": False,
            "retry_count": state.get("retry_count", 0) + 1,
            "execution_error": None,
            "execution_error_type": None,
        }

    def mock_contract(state):
        calls.append("contract")
        return {"contract_valid": True}

    graph = build_recovery_test_graph(
        mock_executor,
        mock_repair,
        mock_contract,
    )

    result = graph.invoke({
        "sql": "SELECT nonexistent_column FROM orders",
        "retry_count": 0,
    })

    assert calls == ["execute", "repair", "execute"]
    assert result["retry_count"] == 1
    assert result["execution_error_type"] == "undefined_column"
