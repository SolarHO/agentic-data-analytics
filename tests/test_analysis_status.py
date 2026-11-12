
from app.agents.recovery_finalizer import (
    finalize_recovery,
    resolve_analysis_status,
)


def test_completed_analysis():
    state = {
        "sql_valid": True,
        "semantic_status": "VALID",
        "execution_error": None,
        "contract_valid": True,
        "result": [{"delay_rate_pct": 8.11}],
    }

    result = finalize_recovery(state)

    assert result["analysis_status"] == "COMPLETED"
    assert result["analysis_error"] is None
    assert result["recovery_status"] == "not_attempted"


def test_semantic_invalid_is_blocked():
    state = {
        "sql_valid": True,
        "semantic_status": "INVALID",
        "semantic_error": "delivered status missing",
        "execution_error": None,
    }

    result = finalize_recovery(state)

    assert result["analysis_status"] == "BLOCKED"
    assert "delivered status missing" in result["analysis_error"]


def test_semantic_unsupported_is_blocked():
    state = {
        "sql_valid": True,
        "semantic_status": "UNSUPPORTED",
        "semantic_error": "Unsupported aggregate",
        "execution_error": None,
    }

    status, error = resolve_analysis_status(state)

    assert status == "BLOCKED"
    assert "Unsupported aggregate" in error


def test_execution_error_is_failed():
    state = {
        "sql_valid": True,
        "semantic_status": "VALID",
        "execution_error": "column does not exist",
        "contract_valid": False,
    }

    result = finalize_recovery(state)

    assert result["analysis_status"] == "FAILED"
    assert result["analysis_error"] == "column does not exist"


def test_contract_failure_is_failed():
    state = {
        "sql_valid": True,
        "semantic_status": "VALID",
        "execution_error": None,
        "contract_valid": False,
        "contract_error": "Missing metric column",
    }

    result = finalize_recovery(state)

    assert result["analysis_status"] == "FAILED"
    assert result["analysis_error"] == "Missing metric column"


def test_missing_contract_cannot_be_completed():
    state = {
        "sql_valid": True,
        "semantic_status": "VALID",
        "execution_error": None,
    }

    result = finalize_recovery(state)

    assert result["analysis_status"] == "FAILED"
