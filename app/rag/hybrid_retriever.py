
from psycopg import connect
from psycopg.rows import dict_row

from app.graph.metric_plan import MetricPlan
from app.rag.context_resolver import resolve_required_document_ids
from app.rag.retriever import (
    get_read_connection_info,
    search_context,
)


def get_documents_by_ids(
    document_ids: set[str],
) -> list[dict]:
    """Fetch required documents by their IDs."""

    if not document_ids:
        return []

    with connect(
        **get_read_connection_info(),
        row_factory=dict_row,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    document_id,
                    doc_type,
                    name,
                    content,
                    embedding_model
                FROM public.rag_documents
                WHERE document_id = ANY(%s)
                """,
                (sorted(document_ids),),
            )

            return cursor.fetchall()


def hybrid_search_context(
    question: str,
    metric_plan: MetricPlan,
    vector_top_k: int = 5,
    max_documents: int = 15,
) -> list[dict]:
    """
    Merge required context with semantic search results.

    Required documents are never silently dropped.
    The final result contains at most max_documents.
    """

    if not question.strip():
        raise ValueError("Question must not be empty.")

    if not 1 <= vector_top_k <= 33:
        raise ValueError(
            "vector_top_k must be between 1 and 33."
        )

    if max_documents < 1:
        raise ValueError(
            "max_documents must be positive."
        )

    # 1. Resolve document dependencies from MetricPlan.
    required_ids = resolve_required_document_ids(
        metric_plan
    )

    if len(required_ids) > max_documents:
        raise ValueError(
            "Required documents exceed max_documents: "
            f"{len(required_ids)} > {max_documents}"
        )

    # 2. Fetch required documents.
    required_documents = get_documents_by_ids(
        required_ids
    )

    found_ids = {
        doc["document_id"]
        for doc in required_documents
    }

    missing_ids = required_ids - found_ids

    if missing_ids:
        raise ValueError(
            "Required documents not found: "
            f"{sorted(missing_ids)}"
        )

    # 3. Retrieve additional semantic candidates.
    vector_results = search_context(
        question=question,
        top_k=vector_top_k,
    )

    vector_lookup = {
        doc["document_id"]: doc
        for doc in vector_results
    }

    # 4. Required documents always come first.
    merged = []
    seen = set()

    for doc in sorted(
        required_documents,
        key=lambda item: item["document_id"],
    ):
        document_id = doc["document_id"]

        vector_match = vector_lookup.get(
            document_id
        )

        merged.append({
            **doc,
            "similarity": (
                vector_match["similarity"]
                if vector_match is not None
                else None
            ),
            "retrieval_source": "required",
        })

        seen.add(document_id)

    # 5. Fill remaining slots with vector candidates.
    for doc in vector_results:
        if len(merged) >= max_documents:
            break

        document_id = doc["document_id"]

        if document_id in seen:
            continue

        merged.append({
            **doc,
            "retrieval_source": "vector",
        })

        seen.add(document_id)

    return merged
