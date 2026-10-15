
from app.agents.output_contract_validator import (
    validate_output_contract,
)
from app.graph.metric_plan import MetricPlan


def make_plan():
    return MetricPlan.model_validate({
        "intent": "trend",
        "metrics": [
            {
                "name": "product_revenue",
                "description": "Monthly product revenue",
            }
        ],
        "filters": ["order_status = 'delivered'"],
        "dimensions": ["month"],
    })


def test_valid_metric_and_dimension():
    state = {
        "metric_plan": make_plan(),
        "result": [
            {"month": "2017-01", "product_revenue": 1000}
        ],
        "execution_error": None,
    }

    result = validate_output_contract(state)

    assert result["contract_valid"] is True


def test_missing_dimension():
    state = {
        "metric_plan": make_plan(),
        "result": [
            {"product_revenue": 1000}
        ],
        "execution_error": None,
    }

    result = validate_output_contract(state)

    assert result["contract_valid"] is False
    assert "month" in result["contract_error"]


def test_unexpected_column():
    state = {
        "metric_plan": make_plan(),
        "result": [
            {
                "month": "2017-01",
                "product_revenue": 1000,
                "extra_metric": 10,
            }
        ],
        "execution_error": None,
    }

    result = validate_output_contract(state)

    assert result["contract_valid"] is False
    assert "extra_metric" in result["contract_error"]
