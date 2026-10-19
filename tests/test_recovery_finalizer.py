
from app.agents.recovery_finalizer import finalize_recovery


def make_history():
    return [
        {
            "attempt": 1,
            "failed_sql": "SELECT invalid_column FROM orders",
            "error_type": "undefined_column",
            "repaired_sql": "SELECT COUNT(*) FROM orders",
        }
    ]


def test_recovery_success():
    state = {
        "sql_recovery_history": make_history(),
        "execution_error": None,
        "contract_valid": True,
    }

    result = finalize_recovery(state)

    assert result["recovery_status"] == "recovered"
    assert result["sql_recovery_history"][-1]["status"] == "recovered"


def test_recovery_execution_failure():
    state = {
        "sql_recovery_history": make_history(),
        "execution_error": "column does not exist",
        "contract_valid": False,
    }

    result = finalize_recovery(state)

    assert result["recovery_status"] == "failed"
    assert result["sql_recovery_history"][-1]["status"] == "failed"


def test_recovery_contract_failure():
    state = {
        "sql_recovery_history": make_history(),
        "execution_error": None,
        "contract_valid": False,
    }

    result = finalize_recovery(state)

    assert result["recovery_status"] == "failed"


def test_recovery_not_attempted():
    state = {
        "sql_recovery_history": [],
        "execution_error": None,
        "contract_valid": True,
    }

    result = finalize_recovery(state)

    assert result["recovery_status"] == "not_attempted"
