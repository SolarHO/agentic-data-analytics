
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.context.database_context import (
    DATABASE_SCHEMA,
    BUSINESS_RULES,
)
from app.context.dimension_registry import DIMENSION_REGISTRY
from app.graph.state import AnalysisState

load_dotenv()

llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0,
)

SYSTEM_PROMPT = """
You are a PostgreSQL SQL repair agent.

Repair a failed SQL query using the database schema,
business rules, metric plan, and PostgreSQL error.

DATABASE SCHEMA
---------------
{database_schema}

BUSINESS RULES
--------------
{business_rules}

DIMENSION REGISTRY
------------------
{dimension_registry}

METRIC PLAN
-----------
{metric_plan}

FAILED SQL
----------
{failed_sql}

POSTGRESQL ERROR
----------------
{execution_error}

REPAIR RULES
------------
- Generate exactly one corrected PostgreSQL query.
- Only SELECT queries or queries beginning with WITH are allowed.
- Use only tables and columns in the provided schema.
- Preserve the original business meaning and metric definitions.
- Use the exact metric names from the metric plan as output aliases.
- Use the exact dimension names from the metric plan as output aliases.
- Include all requested metrics and dimensions.
- Do not add unrequested output columns.
- Do not remove required filters to avoid an error.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
- Do not execute SQL.
- Return SQL only, without Markdown fences or explanations.
"""


def repair_sql(state: AnalysisState) -> AnalysisState:
    metric_plan = state.get("metric_plan")

    if metric_plan is None:
        raise ValueError("Metric plan is missing.")

    failed_sql = state.get("sql", "").strip()
    execution_error = state.get("execution_error", "")
    question = state.get("question", "").strip()

    if not failed_sql or not execution_error or not question:
        raise ValueError("SQL repair requires question, SQL, and error.")

    prompt = SYSTEM_PROMPT.format(
        database_schema=DATABASE_SCHEMA,
        business_rules=BUSINESS_RULES,
        dimension_registry=DIMENSION_REGISTRY,
        metric_plan=json.dumps(
            metric_plan.model_dump(),
            ensure_ascii=False,
            indent=2,
        ),
        failed_sql=failed_sql,
        execution_error=execution_error,
    )

    response = llm.invoke([
        ("system", prompt),
        ("human", question),
    ])

    corrected_sql = str(response.content).strip()

    # LLM이 수정한 SQL을 생성한 후 복구 이력 기록
    recovery_record = {
        "attempt": state.get("retry_count", 0) + 1,
        "failed_sql": failed_sql,
        "error_type": state.get("execution_error_type"),
        "repaired_sql": corrected_sql,
    }

    return {
        "sql": corrected_sql,
        "sql_valid": False,
        "validation_error": None,
        "result": [],
        "execution_error": None,
        "execution_error_type": None,
        "contract_valid": False,
        "contract_error": None,
        "retry_count": state.get("retry_count", 0) + 1,
        "sql_recovery_history": [
            *state.get("sql_recovery_history", []),
            recovery_record,
        ],
    }
