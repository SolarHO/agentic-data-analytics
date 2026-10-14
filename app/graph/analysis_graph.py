from langgraph.graph import END, START, StateGraph

from app.agents.metric_planner import plan_metrics
from app.agents.sql_generator import generate_sql
from app.agents.sql_validator import validate_sql
from app.agents.sql_executor import execute_sql
from app.agents.output_contract_validator import validate_output_contract

from app.graph.state import AnalysisState


def build_analysis_graph():
    builder = StateGraph(AnalysisState)

    builder.add_node("metric_planner", plan_metrics)
    builder.add_node("sql_generator", generate_sql)
    builder.add_node("sql_validator", validate_sql)
    builder.add_node("sql_executor", execute_sql)

    builder.add_edge(START, "metric_planner")
    builder.add_edge("metric_planner", "sql_generator")
    builder.add_edge("sql_generator", "sql_validator")
    builder.add_edge("sql_validator", "sql_executor")
    builder.add_edge(
        "sql_executor",
        "output_contract_validator",
    )
    builder.add_edge("output_contract_validator", END)

    builder.add_node(
        "output_contract_validator",
        validate_output_contract,
    )

    return builder.compile()


analysis_graph = build_analysis_graph()