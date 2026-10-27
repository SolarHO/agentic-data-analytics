
import json
import re
from pathlib import Path

from app.context.database_context import (
    DATABASE_SCHEMA,
    BUSINESS_RULES,
)
from app.context.metric_registry import METRIC_REGISTRY
from app.context.dimension_registry import DIMENSION_REGISTRY


TABLE_PATTERN = re.compile(
    r"^TABLE\s+(\w+)\s*\n(.*?)"
    r"(?=^TABLE\s+|^Important:|\Z)",
    re.MULTILINE | re.DOTALL,
)

RULE_PATTERN = re.compile(
    r"^(\d+)\.\s+([^\n]+)\n(.*?)"
    r"(?=^\d+\.\s+|^General SQL rules:|\Z)",
    re.MULTILINE | re.DOTALL,
)


def build_rag_documents() -> list[dict]:
    documents = []

    # 1. Table schema documents
    for match in TABLE_PATTERN.finditer(DATABASE_SCHEMA):
        table_name = match.group(1)
        table_details = match.group(2).strip()

        documents.append({
            "id": f"schema:{table_name}",
            "doc_type": "schema",
            "name": table_name,
            "content": (
                f"PostgreSQL Olist table: {table_name}\n"
                f"{table_details}"
            ),
        })

    # 2. Business rule documents
    for match in RULE_PATTERN.finditer(BUSINESS_RULES):
        rule_number = int(match.group(1))
        rule_name = match.group(2).strip()
        rule_details = match.group(3).strip()

        documents.append({
            "id": f"business_rule:{rule_number}",
            "doc_type": "business_rule",
            "name": rule_name,
            "content": (
                f"Business rule: {rule_name}\n"
                f"{rule_details}"
            ),
        })

    # 3. Metric registry documents
    for name, definition in METRIC_REGISTRY.items():
        documents.append({
            "id": f"metric:{name}",
            "doc_type": "metric",
            "name": name,
            "content": (
                f"Metric: {name}\n"
                f"Description: {definition['description']}\n"
                f"Unit: {definition['unit']}"
            ),
        })

    # 4. Dimension registry documents
    for name, definition in DIMENSION_REGISTRY.items():
        documents.append({
            "id": f"dimension:{name}",
            "doc_type": "dimension",
            "name": name,
            "content": (
                f"Dimension: {name}\n"
                f"Description: {definition['description']}\n"
                f"SQL expression: {definition['expression']}\n"
                f"Unit: {definition['unit']}"
            ),
        })

    # 5. Important schema notes
    if "Important:" in DATABASE_SCHEMA:
        notes = DATABASE_SCHEMA.split("Important:", 1)[1].strip()

        documents.append({
            "id": "context:schema_notes",
            "doc_type": "context",
            "name": "Schema Notes",
            "content": f"Important schema notes:\n{notes}",
        })

    # 6. General SQL generation rules
    if "General SQL rules:" in BUSINESS_RULES:
        rules = BUSINESS_RULES.split(
            "General SQL rules:", 1
        )[1].strip()

        documents.append({
            "id": "context:sql_rules",
            "doc_type": "context",
            "name": "General SQL Rules",
            "content": f"General SQL rules:\n{rules}",
        })

    return documents


def save_rag_documents(output_path: Path) -> None:
    documents = build_rag_documents()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            documents,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    output = Path("data/rag/schema_documents.json")
    save_rag_documents(output)

    print(f"RAG documents saved: {output}")
    print(f"Document count: {len(build_rag_documents())}")
