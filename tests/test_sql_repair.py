
from unittest.mock import Mock

import pytest

from app.agents import sql_repair


def make_metric_plan():
    metric_plan = Mock()
    metric_plan.model_dump.return_value = {
        "metrics": ["delivered_orders"],
        "dimensions": [],
    }
    return metric_plan


def test_repair_sql_resets_state(monkeypatch):
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(
        content="SELECT COUNT(*) AS delivered_orders FROM orders"
    )

    monkeypatch.setattr(sql_repair, "llm", mock_llm)

    state = {
        "question": "배송 완료 주문 수는?",
        "metric_plan": make_metric_plan(),
        "sql": "SELECT invalid_column FROM orders",
        "sql_valid": True,
        "validation_error": None,
        "execution_error": "column invalid_column does not exist",
        "execution_error_type": "undefined_column",
        "result": [],
        "contract_valid": False,
        "contract_error": None,
        "retry_count": 0,
    }

    result = sql_repair.repair_sql(state)

    assert result["sql"] == (
        "SELECT COUNT(*) AS delivered_orders FROM orders"
    )
    assert result["retry_count"] == 1
    assert result["sql_valid"] is False
    assert result["validation_error"] is None
    assert result["execution_error"] is None
    assert result["execution_error_type"] is None
    assert result["result"] == []
    assert result["contract_valid"] is False
    assert result["contract_error"] is None
    assert result["sql_recovery_history"] == [
        {
            "attempt": 1,
            "failed_sql": "SELECT invalid_column FROM orders",
            "error_type": "undefined_column",
            "repaired_sql": (
                "SELECT COUNT(*) AS delivered_orders FROM orders"
            ),
        }
    ]

    mock_llm.invoke.assert_called_once()

    messages = mock_llm.invoke.call_args.args[0]
    system_prompt = messages[0][1]

    assert "SELECT invalid_column FROM orders" in system_prompt
    assert "column invalid_column does not exist" in system_prompt


def test_repair_sql_increments_retry_count(monkeypatch):
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(
        content="SELECT COUNT(*) AS delivered_orders FROM orders"
    )

    monkeypatch.setattr(sql_repair, "llm", mock_llm)

    state = {
        "question": "배송 완료 주문 수는?",
        "metric_plan": make_metric_plan(),
        "sql": "SELECT invalid_column FROM orders",
        "execution_error": "column does not exist",
        "retry_count": 1,
    }

    result = sql_repair.repair_sql(state)

    assert result["retry_count"] == 2


@pytest.mark.parametrize(
    "missing_field",
    ["question", "sql", "execution_error", "metric_plan"],
)
def test_repair_sql_requires_input(missing_field, monkeypatch):
    mock_llm = Mock()
    monkeypatch.setattr(sql_repair, "llm", mock_llm)

    state = {
        "question": "배송 완료 주문 수는?",
        "metric_plan": make_metric_plan(),
        "sql": "SELECT invalid_column FROM orders",
        "execution_error": "column does not exist",
        "retry_count": 0,
    }

    state.pop(missing_field)

    with pytest.raises(ValueError):
        sql_repair.repair_sql(state)

    mock_llm.invoke.assert_not_called()
