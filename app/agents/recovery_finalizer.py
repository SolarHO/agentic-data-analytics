
from app.graph.state import AnalysisState


def resolve_analysis_status(state: AnalysisState) -> tuple[str, str | None]:
    """
    Determine the final outcome of an analysis.

    Never infer success solely from execution_error=None.
    """

    # SQL AST validation failed
    if state.get("sql_valid") is False:
        return (
            "BLOCKED",
            state.get("validation_error")
            or "SQL AST validation failed.",
        )

    # Semantic validation blocked execution
    semantic_status = state.get("semantic_status")

    if semantic_status in {"INVALID", "UNSUPPORTED"}:
        return (
            "BLOCKED",
            state.get("semantic_error")
            or f"SQL semantic validation: {semantic_status}",
        )

    # PostgreSQL execution failed
    if state.get("execution_error") is not None:
        return (
            "FAILED",
            state["execution_error"],
        )

    # Output contract validation failed
    if state.get("contract_valid") is False:
        return (
            "FAILED",
            state.get("contract_error")
            or "Output contract validation failed.",
        )

    # Only an explicitly verified result can succeed
    if (
        state.get("sql_valid") is True
        and semantic_status in {"VALID", "SKIPPED"}
        and state.get("contract_valid") is True
        and state.get("execution_error") is None
    ):
        return ("COMPLETED", None)

    return (
        "FAILED",
        "Analysis did not reach a verified successful state.",
    )


def finalize_recovery(state: AnalysisState) -> dict:
    analysis_status, analysis_error = resolve_analysis_status(state)

    history = state.get("sql_recovery_history", [])

    output = {
        "analysis_status": analysis_status,
        "analysis_error": analysis_error,
    }

    if not history:
        output["recovery_status"] = "not_attempted"
        return output

    recovery_status = (
        "recovered"
        if analysis_status == "COMPLETED"
        else "failed"
    )

    updated_history = [
        dict(record)
        for record in history
    ]

    updated_history[-1]["status"] = recovery_status

    output.update({
        "recovery_status": recovery_status,
        "sql_recovery_history": updated_history,
    })

    return output
