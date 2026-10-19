
import pytest

from langgraph.graph import END, START, StateGraph

from app.graph.state import AnalysisState
from app.graph.analysis_graph import (
    route_after_sql_validation,
    route_after_sql_execution,
)
from app.agents.sql_validator import validate_sql
from app.agents.recovery_finalizer import finalize_recovery


def build_test_graph(executor, repair, contract):
    builder = StateGraph(AnalysisState)

    builder.add_node("sql_validator", validate_sql)
    builder.add_node("sql_executor", executor)
    builder.add_node("sql_repair", repair)
    builder.add_node("output_contract_validator", contract)
    builder.add_node("recovery_finalizer", finalize_recovery)

    builder.add_edge(START, "sql_validator")

    builder.add_conditional_edges(
        "sql_validator",
        route_after_sql_validation,
        {
            "execute": "sql_executor",
            "stop": "recovery_finalizer",
        },
    )

    builder.add_conditional_edges(
        "sql_executor",
        route_after_sql_execution,
        {
            "success": "output_contract_validator",
            "retry": "sql_repair",
            "stop": "recovery_finalizer",
        },
    )

    builder.add_edge("sql_repair", "sql_validator")
    builder.add_edge(
        "output_contract_validator",
        "recovery_finalizer",
    )
    builder.add_edge("recovery_finalizer", END)

    return builder.compile()


@pytest.mark.parametrize(
    "scenario, expected_status, expected_calls",
    [
        ("initial_success", "not_attempted", ["execute", "contract"]),
        (
            "recovery_success",
            "recovered",
            ["execute", "repair", "execute", "contract"],
        ),
        (
            "recovery_failure",
            "failed",
            ["execute", "repair", "execute"],
        ),
    ],
)
def test_recovery_finalizer_routing(
    scenario,
    expected_status,
    expected_calls,
):
    calls = []

    def mock_executor(state):
        calls.append("execute")

        if scenario == "initial_success":
            return {
                "execution_error": None,
                "execution_error_type": None,
                "result": [{"delivered_orders": 96478}],
            }

        if state.get("retry_count", 0) == 0:
            return {
                "execution_error": "column does not exist",
                "execution_error_type": "undefined_column",
                "result": [],
            }

        if scenario == "recovery_success":
            return {
                "execution_error": None,
                "execution_error_type": None,
                "result": [{"delivered_orders": 96478}],
            }

        return {
            "execution_error": "column still does not exist",
            "execution_error_type": "undefined_column",
            "result": [],
        }

    def mock_repair(state):
        calls.append("repair")

        original_sql = state["sql"]
        repaired_sql = (
            "SELECT COUNT(*) AS delivered_orders FROM orders"
        )

        return {
            "sql": repaired_sql,
            "sql_valid": False,
            "retry_count": state.get("retry_count", 0) + 1,
            "execution_error": None,
            "execution_error_type": None,
            "sql_recovery_history": [
                *state.get("sql_recovery_history", []),
                {
                    "attempt": 1,
                    "failed_sql": original_sql,
                    "error_type": "undefined_column",
                    "repaired_sql": repaired_sql,
                },
            ],
        }

    def mock_contract(state):
        calls.append("contract")
        return {"contract_valid": True}

    graph = build_test_graph(
        mock_executor,
        mock_repair,
        mock_contract,
    )

    result = graph.invoke({
        "sql": "SELECT nonexistent_column FROM orders",
        "retry_count": 0,
    })

    assert calls == expected_calls
    assert result["recovery_status"] == expected_status

    if scenario == "initial_success":
        assert not result.get("sql_recovery_history")
    else:
        assert result["retry_count"] == 1
        assert result["sql_recovery_history"][-1]["status"] == expected_status
