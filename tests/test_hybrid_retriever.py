
import pytest

from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)
from app.rag import hybrid_retriever


def make_plan():
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name="product_revenue",
                description="Product revenue",
            )
        ],
        dimensions=["category"],
        filters=[],
    )


def make_document(document_id):
    return {
        "document_id": document_id,
        "doc_type": document_id.split(":")[0],
        "name": document_id,
        "content": f"Content for {document_id}",
        "embedding_model": "test-model",
    }


def test_required_documents_are_preserved(
    monkeypatch,
):
    required_ids = {
        "metric:product_revenue",
        "dimension:category",
        "schema:products",
    }

    monkeypatch.setattr(
        hybrid_retriever,
        "resolve_required_document_ids",
        lambda plan: required_ids,
    )

    monkeypatch.setattr(
        hybrid_retriever,
        "get_documents_by_ids",
        lambda ids: [
            make_document(doc_id)
            for doc_id in ids
        ],
    )

    monkeypatch.setattr(
        hybrid_retriever,
        "search_context",
        lambda question, top_k: [
            {
                **make_document("metric:product_revenue"),
                "similarity": 0.9,
            },
            {
                **make_document("metric:average_order_value"),
                "similarity": 0.8,
            },
        ],
    )

    results = hybrid_retriever.hybrid_search_context(
        question="카테고리별 매출",
        metric_plan=make_plan(),
        vector_top_k=2,
        max_documents=4,
    )

    result_ids = [
        doc["document_id"]
        for doc in results
    ]

    assert len(results) == 4
    assert required_ids <= set(result_ids)
    assert len(result_ids) == len(set(result_ids))

    assert "metric:average_order_value" in result_ids

    assert sum(
        doc["retrieval_source"] == "required"
        for doc in results
    ) == 3


def test_required_documents_exceed_budget(
    monkeypatch,
):
    monkeypatch.setattr(
        hybrid_retriever,
        "resolve_required_document_ids",
        lambda plan: {"a", "b", "c"},
    )

    with pytest.raises(
        ValueError,
        match="exceed max_documents",
    ):
        hybrid_retriever.hybrid_search_context(
            question="test",
            metric_plan=make_plan(),
            max_documents=2,
        )


def test_missing_required_documents(
    monkeypatch,
):
    monkeypatch.setattr(
        hybrid_retriever,
        "resolve_required_document_ids",
        lambda plan: {"schema:orders"},
    )

    monkeypatch.setattr(
        hybrid_retriever,
        "get_documents_by_ids",
        lambda ids: [],
    )

    with pytest.raises(
        ValueError,
        match="Required documents not found",
    ):
        hybrid_retriever.hybrid_search_context(
            question="test",
            metric_plan=make_plan(),
        )


def test_empty_question_rejected():
    with pytest.raises(
        ValueError,
        match="Question must not be empty",
    ):
        hybrid_retriever.hybrid_search_context(
            question=" ",
            metric_plan=make_plan(),
        )


def test_vector_results_respect_document_budget(
    monkeypatch,
):
    required_ids = {"schema:orders"}

    monkeypatch.setattr(
        hybrid_retriever,
        "resolve_required_document_ids",
        lambda plan: required_ids,
    )

    monkeypatch.setattr(
        hybrid_retriever,
        "get_documents_by_ids",
        lambda ids: [make_document("schema:orders")],
    )

    monkeypatch.setattr(
        hybrid_retriever,
        "search_context",
        lambda question, top_k: [
            {
                **make_document(f"metric:test_{i}"),
                "similarity": 0.5,
            }
            for i in range(5)
        ],
    )

    results = hybrid_retriever.hybrid_search_context(
        question="test",
        metric_plan=make_plan(),
        max_documents=3,
    )

    assert len(results) == 3
    assert results[0]["document_id"] == "schema:orders"
