
from app.agents.sql_executor import execute_sql
from app.agents.sql_repair import repair_sql
from app.agents.sql_validator import validate_sql
from app.graph.metric_plan import MetricPlan, MetricDefinition
from app.graph.analysis_graph import route_after_sql_execution


def main():
    failed_sql = """
    SELECT COUNT(nonexistent_column) AS delivered_orders
    FROM orders
    WHERE order_status = 'delivered'
    """

    state = {
        "question": "배송 완료된 주문 수를 알려줘.",
        "metric_plan": MetricPlan(
            intent="aggregation",
            metrics=[
                MetricDefinition(
                    name="delivered_orders",
                    description=(
                        "배송 완료된 주문의 고유 주문 수"
                    ),
                )
            ],
            filters=["order_status = 'delivered'"],
            dimensions=[],
        ),
        "sql": failed_sql,
        "sql_valid": True,
        "retry_count": 0,
    }

    print("=== 1. Execute invalid SQL ===")
    state.update(execute_sql(state))

    print("Error type:", state.get("execution_error_type"))

    assert state["execution_error_type"] == "undefined_column"

    route = route_after_sql_execution(state)
    print("Route:", route)

    assert route == "retry"

    print("\n=== 2. Repair SQL ===")
    state.update(repair_sql(state))

    print("Repaired SQL:")
    print(state["sql"])
    print("Retry count:", state["retry_count"])

    assert state["retry_count"] == 1

    print("\n=== 3. Validate repaired SQL ===")
    state.update(validate_sql(state))

    print("SQL valid:", state["sql_valid"])

    if not state["sql_valid"]:
        raise RuntimeError(
            f"Repaired SQL failed validation: "
            f"{state.get('validation_error')}"
        )

    print("\n=== 4. Execute repaired SQL ===")
    state.update(execute_sql(state))

    print("Result:", state["result"])
    print("Error:", state["execution_error"])

    assert state["execution_error"] is None
    assert len(state["result"]) == 1
    assert state["result"][0]["delivered_orders"] == 96478
    assert state["retry_count"] == 1

    print("\nSQL Repair E2E: PASS")


if __name__ == "__main__":
    main()
