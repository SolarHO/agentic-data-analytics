from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_value(value: Any) -> Any:
    """
    Normalize numeric values for evaluation.

    Numeric values are rounded to 2 decimal places so that values such as
    Decimal('137.041585...') can be compared with Decimal('137.04').
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value)).quantize(Decimal("0.01"))
        except InvalidOperation:
            return value

    return value



def compare_result(
    actual: list[dict[str, Any]],
    expected: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Compare single-row SQL results using canonical metric names.
    """
    errors: list[str] = []

    if not actual:
        return False, ["Query returned no rows."]

    if len(actual) != 1:
        return False, [
            f"Expected 1 row, but query returned {len(actual)} rows."
        ]

    actual_row = actual[0]

    expected_columns = set(expected.keys())
    actual_columns = set(actual_row.keys())

    missing_columns = expected_columns - actual_columns
    unexpected_columns = actual_columns - expected_columns

    if missing_columns:
        errors.append(
            f"Missing columns: {sorted(missing_columns)}"
        )

    if unexpected_columns:
        errors.append(
            f"Unexpected columns: {sorted(unexpected_columns)}"
        )

    for metric_name, expected_value in expected.items():
        if metric_name not in actual_row:
            continue

        actual_value = actual_row[metric_name]

        normalized_actual = normalize_value(actual_value)
        normalized_expected = normalize_value(expected_value)

        if normalized_actual != normalized_expected:
            errors.append(
                f"{metric_name}: expected {expected_value}, "
                f"got {actual_value}"
            )

    return len(errors) == 0, errors
