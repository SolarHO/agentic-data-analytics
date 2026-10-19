
from langgraph.graph import END, START, StateGraph

from app.agents.metric_planner import plan_metrics
from app.agents.sql_validator import validate_sql
from app.agents.sql_executor import execute_sql
from app.agents.sql_repair import repair_sql
from app.agents.output_contract_validator import (
    validate_output_contract,
)
from app.agents.recovery_finalizer import finalize_recovery
from app.graph.analysis_graph import (
    route_after_sql_validation,
    route_after_sql_execution,
)
from app.graph.state import AnalysisState


def generate_invalid_sql(state: AnalysisState):
    return {
        "sql": (
            "SELECT COUNT(nonexistent_column) AS delivered_orders "
            "FROM orders WHERE order_status = 'delivered'"
        ),
        "sql_valid": False,
    }


def build_test_graph():
    builder = StateGraph(AnalysisState)

    builder.add_node("metric_planner", plan_metrics)
    builder.add_node("sql_generator", generate_invalid_sql)
    builder.add_node("sql_validator", validate_sql)
    builder.add_node("sql_executor", execute_sql)
    builder.add_node("sql_repair", repair_sql)
    builder.add_node(
        "output_contract_validator",
        validate_output_contract,
    )
    builder.add_node(
        "recovery_finalizer",
        finalize_recovery,
    )

    builder.add_edge(START, "metric_planner")
    builder.add_edge("metric_planner", "sql_generator")
    builder.add_edge("sql_generator", "sql_validator")

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
    builder.add_edge("output_contract_validator","recovery_finalizer")

    builder.add_edge("recovery_finalizer", END)

    return builder.compile()


def main():
    graph = build_test_graph()

    result = graph.invoke({
        "question": "배송 완료된 주문 수를 알려줘.",
        "retry_count": 0,
    })

    print("=== Graph Recovery E2E ===")
    print("Final SQL:", result.get("sql"))
    print("Retry Count:", result.get("retry_count"))
    print("SQL Valid:", result.get("sql_valid"))
    print("Execution Error:", result.get("execution_error"))
    print("Contract Valid:", result.get("contract_valid"))
    print("Result:", result.get("result"))
    print("Recovery History:", result.get("sql_recovery_history"))
    print("Recovery Status:", result.get("recovery_status"))

    assert result.get("retry_count") == 1
    assert result.get("execution_error") is None
    assert result.get("sql_valid") is True
    assert result.get("contract_valid") is True
    assert result["result"][0]["delivered_orders"] == 96478

    history = result.get("sql_recovery_history", [])

    assert len(history) == 1
    assert history[0]["attempt"] == 1
    assert history[0]["error_type"] == "undefined_column"
    assert "nonexistent_column" in history[0]["failed_sql"]
    assert history[0]["repaired_sql"] == result["sql"]

    assert result["recovery_status"] == "recovered"
    assert result["sql_recovery_history"][-1]["status"] == "recovered"

    print("\nGraph Recovery E2E: PASS")


if __name__ == "__main__":
    main()
