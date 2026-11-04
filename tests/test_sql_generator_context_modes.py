
from types import SimpleNamespace

import pytest

from app.agents import sql_generator
from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)


def make_plan():
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name="product_revenue",
                description="Product revenue",
            ),
        ],
        dimensions=["category"],
        filters=[],
    )


def make_state(mode=None):
    state = {
        "question": "카테고리별 매출을 알려줘.",
        "metric_plan": make_plan(),
    }

    if mode is not None:
        state["context_mode"] = mode

    return state


def test_full_mode_contains_original_schema():
    prompt = sql_generator.build_sql_prompt(
        question="매출을 알려줘.",
        metric_plan=make_plan(),
        mode="full",
    )

    assert "DATABASE SCHEMA" in prompt
    assert "BUSINESS RULES" in prompt
    assert "TABLE orders" in prompt
    assert "TABLE geolocation" in prompt


def test_registry_mode_uses_retrieved_context(monkeypatch):
    monkeypatch.setattr(
        sql_generator,
        "get_context_documents",
        lambda question, metric_plan, mode: [
            {
                "document_id": "schema:orders",
                "content": "TABLE orders\n- order_id",
            },
        ],
    )

    prompt = sql_generator.build_sql_prompt(
        question="매출을 알려줘.",
        metric_plan=make_plan(),
        mode="registry",
    )

    assert "RETRIEVED DATABASE CONTEXT" in prompt
    assert "[schema:orders]" in prompt
    assert "TABLE orders" in prompt
    assert "TABLE geolocation" not in prompt


def test_hybrid_mode_routes_correctly(monkeypatch):
    received = {}

    def fake_documents(question, metric_plan, mode):
        received["mode"] = mode
        return [
            {
                "document_id": "dimension:category",
                "content": "Dimension: category",
            }
        ]

    monkeypatch.setattr(
        sql_generator,
        "get_context_documents",
        fake_documents,
    )

    prompt = sql_generator.build_sql_prompt(
        question="카테고리별 매출",
        metric_plan=make_plan(),
        mode="hybrid",
    )

    assert received["mode"] == "hybrid"
    assert "[dimension:category]" in prompt


def test_invalid_mode_rejected():
    with pytest.raises(
        ValueError,
        match="Unsupported context mode",
    ):
        sql_generator.build_sql_prompt(
            question="매출",
            metric_plan=make_plan(),
            mode="invalid",
        )
        

def test_default_mode_is_full(monkeypatch):
    captured = {}

    class FakeLLM:
        def invoke(self, messages):
            captured["messages"] = messages
            return SimpleNamespace(
                content="SELECT 1 AS product_revenue"
            )

    monkeypatch.setattr(
        sql_generator,
        "llm",
        FakeLLM(),
    )

    result = sql_generator.generate_sql(
        make_state()
    )

    assert "SELECT 1" in result["sql"]
    assert "DATABASE SCHEMA" in captured["messages"][0][1]



def test_retrieval_failure_is_not_hidden(monkeypatch):
    def broken_retriever(question, metric_plan, mode):
        raise ValueError("Required context missing")

    monkeypatch.setattr(
        sql_generator,
        "get_context_documents",
        broken_retriever,
    )

    with pytest.raises(
        ValueError,
        match="Required context missing",
    ):
        sql_generator.generate_sql(
            make_state("registry")
        )
