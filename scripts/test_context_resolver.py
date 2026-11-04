
from psycopg import connect

from app.graph.metric_plan import MetricDefinition, MetricPlan
from app.rag.context_resolver import (
    resolve_required_document_ids,
)
from app.rag.retriever import get_read_connection_info


def main():
    plan = MetricPlan(
        intent="comparison",
        metrics=[
            MetricDefinition(
                name="product_revenue",
                description="Product revenue",
            ),
        ],
        dimensions=["category"],
        filters=[],
    )

    required_ids = resolve_required_document_ids(plan)

    print("Required documents:")
    for doc_id in sorted(required_ids):
        print(f"- {doc_id}")

    with connect(**get_read_connection_info()) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT document_id
                FROM public.rag_documents
                WHERE document_id = ANY(%s)
                """,
                (sorted(required_ids),),
            )

            found_ids = {
                row[0]
                for row in cursor.fetchall()
            }

    missing_ids = required_ids - found_ids

    print()
    print(f"Required: {len(required_ids)}")
    print(f"Found: {len(found_ids)}")
    print(f"Missing: {len(missing_ids)}")

    if missing_ids:
        raise RuntimeError(
            f"Missing documents: {sorted(missing_ids)}"
        )

    print("Registry-only retrieval: PASS")


if __name__ == "__main__":
    main()
