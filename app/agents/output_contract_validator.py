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

    expected_columns = {
        metric.name
        for metric in metric_plan.metrics
    }

    actual_columns = set(result[0].keys())

    missing_columns = expected_columns - actual_columns

    if missing_columns:
        return {
            "contract_valid": False,
            "contract_error": (
                "Missing expected metric columns: "
                + ", ".join(sorted(missing_columns))
            ),
        }

    return {
        "contract_valid": True,
        "contract_error": None,
    }