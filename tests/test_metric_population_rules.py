
from app.context.metric_registry import METRIC_REGISTRY
from app.rag.document_builder import build_rag_documents


DELAY_METRICS = [
    "delivered_orders_with_delivery_date",
    "delayed_orders",
    "delay_rate_pct",
]


def test_delay_metrics_have_mandatory_population():
    for metric_name in DELAY_METRICS:
        definition = METRIC_REGISTRY[metric_name]

        assert definition["required_population"] == [
            "orders.order_status = 'delivered'",
            "orders.order_delivered_customer_date IS NOT NULL",
        ]


def test_delayed_orders_has_calculation_condition():
    definition = METRIC_REGISTRY["delayed_orders"]

    assert (
        definition["calculation_condition"]
        == "orders.order_delivered_customer_date "
           "> orders.order_estimated_delivery_date"
    )


def test_delay_rate_has_formula():
    definition = METRIC_REGISTRY["delay_rate_pct"]

    assert (
        definition["formula"]
        == "100 * delayed_orders / "
           "delivered_orders_with_delivery_date"
    )


def test_rag_documents_include_required_population():
    documents = {
        document["id"]: document
        for document in build_rag_documents()
    }

    for metric_name in DELAY_METRICS:
        content = documents[
            f"metric:{metric_name}"
        ]["content"]

        assert "Mandatory population filters" in content
        assert "orders.order_status = 'delivered'" in content
        assert (
            "orders.order_delivered_customer_date "
            "IS NOT NULL"
        ) in content


def test_rag_document_contains_delay_formula():
    documents = {
        document["id"]: document
        for document in build_rag_documents()
    }

    content = documents["metric:delay_rate_pct"]["content"]

    assert (
        "100 * delayed_orders / "
        "delivered_orders_with_delivery_date"
    ) in content
