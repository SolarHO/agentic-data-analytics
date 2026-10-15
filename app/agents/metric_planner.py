from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from app.context.metric_registry import METRIC_REGISTRY
from app.context.dimension_registry import DIMENSION_REGISTRY
from app.context.database_context import (
    DATABASE_SCHEMA,
    BUSINESS_RULES,
)
from app.graph.metric_plan import MetricPlan
from app.graph.state import AnalysisState

load_dotenv()

llm = ChatOpenAI(
    model="gpt-5-mini",
)

structured_llm = llm.with_structured_output(
    MetricPlan,
    method="json_schema",
)

SYSTEM_PROMPT = """
You are a data analytics planning agent.

Convert a user's natural-language question into a structured
analysis plan.

DATABASE SCHEMA
---------------
{database_schema}

BUSINESS RULES
--------------
{business_rules}

METRIC REGISTRY
---------------
{metric_registry}

DIMENSION REGISTRY
------------------
{dimension_registry}

PLANNING RULES
--------------
- Do not generate SQL.
- Identify the metrics required to answer the question.
- Use only concepts supported by the provided database schema.
- Follow the business rules.
- Use descriptive English snake_case metric names.
- Use the same canonical metric name for the same business meaning.
- Identify relevant filters and grouping dimensions.
- Do not calculate or invent metric values.
- Select metric names only from the METRIC REGISTRY.
- Never invent new metric names.
- Include only final metrics requested by the user.
- Intermediate calculations belong in metric descriptions, not in metrics.
- Filters must contain row filtering conditions only.
- Do not put JOIN instructions or metric formulas in filters.
- Select grouping dimensions only from the DIMENSION REGISTRY.
- Use the exact canonical dimension name.
- Do not invent new dimension names.
- Do not include grouping dimensions in metrics.
"""


def create_metric_plan(question: str) -> MetricPlan:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

    prompt = SYSTEM_PROMPT.format(
        database_schema=DATABASE_SCHEMA,
        business_rules=BUSINESS_RULES,
        metric_registry=METRIC_REGISTRY,
        dimension_registry=DIMENSION_REGISTRY,
    )

    result = structured_llm.invoke(
        [
            ("system", prompt),
            ("human", question),
        ]
    )

    if not isinstance(result, MetricPlan):
        raise TypeError("LLM did not return a valid MetricPlan.")

    return result


def plan_metrics(state: AnalysisState) -> AnalysisState:
    question = state.get("question", "")

    plan = create_metric_plan(question)

    return {
        "metric_plan": plan,
    }