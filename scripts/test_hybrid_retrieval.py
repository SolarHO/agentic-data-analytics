
from app.graph.metric_plan import MetricDefinition, MetricPlan
from app.rag.context_resolver import resolve_required_document_ids
from app.rag.hybrid_retriever import hybrid_search_context


def main():
    question = "상품 카테고리별 매출을 분석해줘."

    metric_plan = MetricPlan(
        intent="comparison",
        metrics=[
            MetricDefinition(
                name="product_revenue",
                description="Product revenue",
            )
        ],
        dimensions=["category"],
        filters=[],
    )

    required_ids = resolve_required_document_ids(
        metric_plan
    )

    results = hybrid_search_context(
        question=question,
        metric_plan=metric_plan,
        vector_top_k=5,
        max_documents=15,
    )

    result_ids = {
        doc["document_id"]
        for doc in results
    }

    missing_ids = required_ids - result_ids

    print("=" * 65)
    print("Question:", question)
    print("Required documents:", len(required_ids))
    print("Retrieved documents:", len(results))
    print("Missing required documents:", len(missing_ids))
    print()

    for index, doc in enumerate(results, start=1):
        similarity = doc.get("similarity")
        similarity_text = (
            f"{similarity:.4f}"
            if similarity is not None
            else "N/A"
        )

        print(
            f"{index:02d}. "
            f"[{doc['retrieval_source']}] "
            f"{doc['document_id']} "
            f"(similarity={similarity_text})"
        )

    if missing_ids:
        raise RuntimeError(
            f"Missing required documents: {sorted(missing_ids)}"
        )

    print()
    print("Hybrid Context Retrieval: PASS")


if __name__ == "__main__":
    main()
