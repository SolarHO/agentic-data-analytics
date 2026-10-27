
from collections import Counter

from app.rag.document_builder import build_rag_documents


def test_document_count():
    documents = build_rag_documents()

    counts = Counter(
        doc["doc_type"] for doc in documents
    )

    assert len(documents) == 33
    assert counts["schema"] == 9
    assert counts["business_rule"] == 7
    assert counts["metric"] == 13
    assert counts["dimension"] == 2
    assert counts["context"] == 2


def test_document_ids_are_unique():
    documents = build_rag_documents()

    ids = [doc["id"] for doc in documents]

    assert len(ids) == len(set(ids))


def test_documents_have_required_fields():
    documents = build_rag_documents()

    for doc in documents:
        assert doc["id"]
        assert doc["doc_type"]
        assert doc["name"]
        assert doc["content"]


def test_aov_business_definition():
    documents = build_rag_documents()

    aov_rule = next(
        doc
        for doc in documents
        if doc["name"] == "Average Order Value (AOV)"
    )

    assert "SUM(order_items.price)" in aov_rule["content"]
    assert "Do NOT calculate AVG(order_items.price)" in (
        aov_rule["content"]
    )


def test_category_dimension_preserves_expression():
    documents = build_rag_documents()

    category = next(
        doc
        for doc in documents
        if doc["id"] == "dimension:category"
    )

    assert "COALESCE(" in category["content"]
    assert "product_category_name_english" in (
        category["content"]
    )
