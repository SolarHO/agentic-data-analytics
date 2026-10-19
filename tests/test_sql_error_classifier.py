
import pytest

from unittest.mock import Mock

from sqlalchemy.exc import ProgrammingError

from app.agents.sql_error_classifier import (
    SQLErrorType,
    classify_sql_error,
    should_retry_sql,
)


@pytest.mark.parametrize(
    "sqlstate, expected_type, expected_retry",
    [
        ("42601", SQLErrorType.SYNTAX_ERROR, True),
        ("42703", SQLErrorType.UNDEFINED_COLUMN, True),
        ("42P01", SQLErrorType.UNDEFINED_TABLE, True),
        ("42501", SQLErrorType.PERMISSION_DENIED, False),
        ("57014", SQLErrorType.QUERY_TIMEOUT, False),
        ("99999", SQLErrorType.UNKNOWN, False),
    ],
)
def test_sqlstate_classification(
    sqlstate,
    expected_type,
    expected_retry,
):
    original_error = Mock()
    original_error.sqlstate = sqlstate

    error = ProgrammingError(
        statement="SELECT invalid_column FROM orders",
        params=None,
        orig=original_error,
    )

    error_type = classify_sql_error(error)

    assert error_type == expected_type
    assert should_retry_sql(error_type) is expected_retry


def test_non_database_error():
    error = ValueError("Invalid application input")

    error_type = classify_sql_error(error)

    assert error_type == SQLErrorType.UNKNOWN
    assert should_retry_sql(error_type) is False
