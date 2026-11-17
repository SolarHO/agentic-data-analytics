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

import logging

logger = logging.getLogger(__name__)

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

METRIC SELECTION RULES
----------------------
- Identify every explicitly requested output metric.
- Do not replace a requested metric with a related metric.
- If the user asks for delayed or late deliveries, select delayed_orders.
- If the user asks for the delivery delay rate or percentage,
  select delay_rate_pct.
- Do not substitute delivered_orders for delayed_orders.
- For count, rate, average, and sum questions, use aggregation
  unless a more specific comparison or trend intent applies.
- Required population conditions already defined in the
  METRIC REGISTRY are part of the metric definition.
- Do not repeat those required population conditions in filters.
- filters must contain only additional restrictions explicitly
  requested by the user, such as a date range or category.
- Do not include intermediate metrics solely to compute
  another metric unless they are explicitly requested outputs.

EXAMPLES
--------
Question: How many delivered orders were delayed?
Metrics: [delayed_orders]
Intent: aggregation
Filters: []

Question: What are the delayed order count and delivery delay rate?
Metrics: [delayed_orders, delay_rate_pct]
Intent: aggregation
Filters: []

Question: What is the delivery delay rate for orders purchased in 2018?
Metrics: [delay_rate_pct]
Intent: aggregation
Filters: [order purchase date in 2018]
``
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

    logger.info(
        "Metric Plan: %s",
        plan.model_dump_json(),
    )

    return {
        "metric_plan": plan,
    }
