import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.context.database_context import (
    DATABASE_SCHEMA,
    BUSINESS_RULES,
)
from app.graph.state import AnalysisState

load_dotenv()

llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0,
)

SYSTEM_PROMPT = """
You are a PostgreSQL data analyst.

Generate a PostgreSQL SELECT query using the user question
and the structured metric plan.

DATABASE SCHEMA
---------------
{database_schema}

BUSINESS RULES
--------------
{business_rules}

METRIC PLAN
-----------
{metric_plan}

SQL GENERATION RULES
--------------------
- Generate exactly one PostgreSQL SELECT query.
- Queries beginning with WITH are also allowed.
- Use only tables and columns defined in the database schema.
- Follow the business rules and metric definitions.
- Return one output column for each metric in the metric plan.
- Use each metric's exact name as its SQL column alias.
- Do not add extra calculated metrics to the final SELECT output.
- Intermediate metrics may be calculated in CTEs or subqueries.
- Include required grouping dimensions in the final SELECT output.
- Use descriptive English snake_case aliases for dimensions.
- Do not invent tables or columns.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
- Return SQL only.
- Do not include Markdown code fences or explanations.
"""


def generate_sql(state: AnalysisState) -> AnalysisState:
    question = state.get("question", "").strip()
    metric_plan = state.get("metric_plan")

    if not question:
        return {
            "sql": "",
            "sql_valid": False,
            "validation_error": "Question is empty.",
        }

    if metric_plan is None:
        return {
            "sql": "",
            "sql_valid": False,
            "validation_error": "Metric plan is missing.",
        }

    plan_json = json.dumps(
        metric_plan.model_dump(),
        ensure_ascii=False,
        indent=2,
    )

    system_prompt = SYSTEM_PROMPT.format(
        database_schema=DATABASE_SCHEMA,
        business_rules=BUSINESS_RULES,
        metric_plan=plan_json,
    )

    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", question),
        ]
    )

    sql = str(response.content).strip()

    return {
        "sql": sql,
    }