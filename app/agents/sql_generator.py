from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.context.database_context import BUSINESS_RULES, DATABASE_SCHEMA
from app.graph.state import AnalysisState


load_dotenv()


llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0,
)


SYSTEM_PROMPT = """
You are a PostgreSQL data analyst.

Your task is to convert the user's natural-language data analysis question
into a valid PostgreSQL SELECT query.

Use only the database schema and business rules provided below.

DATABASE SCHEMA
---------------
{database_schema}

BUSINESS RULES
--------------
{business_rules}

SQL GENERATION RULES
--------------------
- Generate exactly one PostgreSQL query.
- Only SELECT queries or queries beginning with WITH are allowed.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or TRUNCATE.
- Use only tables and columns defined in the provided schema.
- Follow the business metric definitions exactly.
- Do not invent tables or columns.
- Return SQL only.
- Do not include Markdown code fences.
- Do not explain the SQL.
- Use descriptive English snake_case aliases for all calculated or aggregated columns.
- Do not use Korean or other non-English column aliases.
"""


def generate_sql(state: AnalysisState) -> AnalysisState:
    question = state.get("question", "").strip()

    if not question:
        return {
            **state,
            "sql": "",
            "validation_error": "Question is empty.",
        }

    system_prompt = SYSTEM_PROMPT.format(
        database_schema=DATABASE_SCHEMA,
        business_rules=BUSINESS_RULES,
    )

    response = llm.invoke(
        [
            ("system", system_prompt),
            ("human", question),
        ]
    )

    sql = str(response.content).strip()

    return {
        **state,
        "sql": sql,
    }