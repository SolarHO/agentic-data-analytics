from langgraph.graph import END, START, StateGraph

from app.agents.metric_planner import plan_metrics
from app.agents.sql_generator import generate_sql
from app.agents.sql_validator import validate_sql
from app.agents.sql_executor import execute_sql
from app.agents.sql_repair import repair_sql
from app.agents.sql_error_classifier import (
    SQLErrorType,
    should_retry_sql,
)
from app.agents.output_contract_validator import (
    validate_output_contract,
)
from app.agents.recovery_finalizer import finalize_recovery
from app.graph.state import AnalysisState


def route_after_sql_validation(state: AnalysisState) -> str:
    if state.get("sql_valid", False):
        return "execute"

    return "stop"

def route_after_sql_execution(state: AnalysisState) -> str:
    # SQL 실행이 성공한 경우
    if state.get("execution_error") is None:
        return "success"

    # 이미 SQL을 한 번 재생성했다면 종료
    if state.get("retry_count", 0) >= 1:
        return "stop"

    error_type = state.get("execution_error_type")

    try:
        classified_error = SQLErrorType(error_type)
    except (ValueError, TypeError):
        return "stop"

    if should_retry_sql(classified_error):
        return "retry"

    return "stop"

def build_analysis_graph():
    builder = StateGraph(AnalysisState)

    builder.add_node("metric_planner", plan_metrics)
    builder.add_node("sql_generator", generate_sql)
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

    # SQL 검증 결과에 따라 다음 노드 결정
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
    builder.add_edge("output_contract_validator", "recovery_finalizer")
    builder.add_edge("recovery_finalizer",END)

    return builder.compile()


analysis_graph = build_analysis_graph()