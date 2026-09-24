from langgraph.graph import END, START, StateGraph

from app.agents.sql_executor import execute_sql
from app.agents.sql_generator import generate_sql
from app.agents.sql_validator import validate_sql
from app.graph.state import AnalysisState


def build_analysis_graph():
    builder = StateGraph(AnalysisState)

    builder.add_node("sql_generator", generate_sql)
    builder.add_node("sql_validator", validate_sql)
    builder.add_node("sql_executor", execute_sql)

    builder.add_edge(START, "sql_generator")
    builder.add_edge("sql_generator", "sql_validator")
    builder.add_edge("sql_validator", "sql_executor")
    builder.add_edge("sql_executor", END)

    return builder.compile()


analysis_graph = build_analysis_graph()