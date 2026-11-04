
import pytest

from app.rag.context_formatter import (
    format_retrieved_context,
)


def test_format_context():
    documents = [
        {
            "document_id": "schema:orders",
            "content": "TABLE orders\n- order_id",
        },
        {
            "document_id": "metric:product_revenue",
            "content": "Metric: product_revenue",
        },
    ]

    result = format_retrieved_context(documents)

    assert "[schema:orders]" in result
    assert "TABLE orders" in result
    assert "[metric:product_revenue]" in result


def test_duplicate_documents_removed():
    documents = [
        {
            "document_id": "schema:orders",
            "content": "Orders table",
        },
        {
            "document_id": "schema:orders",
            "content": "Orders table",
        },
    ]

    result = format_retrieved_context(documents)

    assert result.count("[schema:orders]") == 1


def test_empty_documents_rejected():
    with pytest.raises(ValueError, match="No context"):
        format_retrieved_context([])


def test_empty_content_rejected():
    documents = [
        {
            "document_id": "schema:orders",
            "content": "",
        }
    ]

    with pytest.raises(ValueError, match="Empty document"):
        format_retrieved_context(documents)
