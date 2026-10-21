from unittest.mock import MagicMock, Mock

import pytest

from app.agents import sql_executor


@pytest.mark.parametrize(
    "row_count, should_exceed",
    [
        (0, False),
        (999, False),
        (1000, False),
        (1001, True),
        (10000, True),
    ],
)
def test_sql_result_row_limit(
    monkeypatch,
    row_count,
    should_exceed,
):
    # Simulate a database result with the specified row count.
    fetched_rows = [
        {"id": index}
        for index in range(row_count)
    ]

    mock_result = Mock()
    mock_result.mappings.return_value.fetchmany.side_effect = (
        lambda size: fetched_rows[:size]
    )

    mock_connection = Mock()
    mock_connection.execute.return_value = mock_result

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = (
        mock_connection
    )

    monkeypatch.setattr(
        sql_executor,
        "read_engine",
        mock_engine,
    )

    result = sql_executor.execute_sql({
        "sql": "SELECT id FROM orders",
        "sql_valid": True,
    })

    mock_result.mappings.return_value.fetchmany.assert_called_once_with(
        sql_executor.MAX_RESULT_ROWS + 1
    )

    if should_exceed:
        assert result["result"] == []
        assert result["execution_error_type"] == (
            "result_limit_exceeded"
        )
        assert result["execution_error"] is not None
    else:
        assert len(result["result"]) == row_count
        assert result["execution_error"] is None
        assert result["execution_error_type"] is None
