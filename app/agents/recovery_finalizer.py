
from app.graph.state import AnalysisState


def finalize_recovery(state: AnalysisState) -> dict:
    history = state.get("sql_recovery_history", [])

    if not history:
        return {
            "recovery_status": "not_attempted",
        }

    if (
        state.get("execution_error") is None
        and state.get("contract_valid") is True
    ):
        status = "recovered"
    else:
        status = "failed"

    updated_history = [
        dict(record)
        for record in history
    ]

    updated_history[-1]["status"] = status

    return {
        "recovery_status": status,
        "sql_recovery_history": updated_history,
    }
