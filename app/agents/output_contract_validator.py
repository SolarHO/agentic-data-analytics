
from app.graph.state import AnalysisState


def validate_output_contract(
    state: AnalysisState,
) -> AnalysisState:
    metric_plan = state.get("metric_plan")
    result = state.get("result", [])

    if metric_plan is None:
        return {
            "contract_valid": False,
            "contract_error": "Metric plan is missing.",
        }

    if state.get("execution_error"):
        return {
            "contract_valid": False,
            "contract_error": "SQL execution failed.",
        }

    if not result:
        return {
            "contract_valid": False,
            "contract_error": "Query returned no rows.",
        }

    expected_metrics = {
        metric.name
        for metric in metric_plan.metrics
    }

    expected_dimensions = set(metric_plan.dimensions)

    expected_columns = expected_metrics | expected_dimensions
    actual_columns = set(result[0].keys())

    missing_columns = expected_columns - actual_columns
    unexpected_columns = actual_columns - expected_columns

    errors = []

    if missing_columns:
        errors.append(
            f"Missing columns: {sorted(missing_columns)}"
        )

    if unexpected_columns:
        errors.append(
            f"Unexpected columns: {sorted(unexpected_columns)}"
        )

    if errors:
        return {
            "contract_valid": False,
            "contract_error": "; ".join(errors),
        }

    return {
        "contract_valid": True,
        "contract_error": None,
    }
