from decimal import Decimal, InvalidOperation
from typing import Any
from datetime import date, datetime


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



from datetime import date, datetime


def normalize_dimension(value: Any, dimension: str) -> str:
    """
    Normalize dimension values for comparison.
    """
    if dimension == "month":
        if isinstance(value, (date, datetime)):
            return value.strftime("%Y-%m")

        value_str = str(value)

        # Supports YYYY-MM-DD and YYYY-MM
        return value_str[:7]

    return str(value)


def compare_multirow_result(
    actual: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    dimension: str,
) -> tuple[bool, list[str]]:
    """
    Compare multi-row SQL results by a dimension key,
    regardless of row order.
    """
    errors: list[str] = []

    def build_index(
        rows: list[dict[str, Any]],
        source: str,
    ) -> dict[str, dict[str, Any]]:
        index = {}

        for row in rows:
            if dimension not in row:
                errors.append(
                    f"{source}: missing dimension column '{dimension}'"
                )
                continue

            key = normalize_dimension(row[dimension], dimension)

            if key in index:
                errors.append(
                    f"{source}: duplicate dimension key '{key}'"
                )
                continue

            index[key] = row

        return index

    expected_index = build_index(expected, "Expected")
    actual_index = build_index(actual, "Actual")

    expected_keys = set(expected_index)
    actual_keys = set(actual_index)

    missing_keys = expected_keys - actual_keys
    unexpected_keys = actual_keys - expected_keys

    if missing_keys:
        errors.append(
            f"Missing dimension keys: {sorted(missing_keys)}"
        )

    if unexpected_keys:
        errors.append(
            f"Unexpected dimension keys: {sorted(unexpected_keys)}"
        )

    for key in sorted(expected_keys & actual_keys):
        expected_row = expected_index[key]
        actual_row = actual_index[key]

        expected_columns = set(expected_row) - {dimension}
        actual_columns = set(actual_row) - {dimension}

        missing_columns = expected_columns - actual_columns
        unexpected_columns = actual_columns - expected_columns

        if missing_columns:
            errors.append(
                f"[{key}] Missing columns: {sorted(missing_columns)}"
            )

        if unexpected_columns:
            errors.append(
                f"[{key}] Unexpected columns: {sorted(unexpected_columns)}"
            )

        for metric_name in expected_columns & actual_columns:
            expected_value = expected_row[metric_name]
            actual_value = actual_row[metric_name]

            if isinstance(expected_value, str) and isinstance(
                actual_value, (int, float, Decimal)
            ):
                expected_value = Decimal(expected_value)

            normalized_expected = normalize_value(expected_value)
            normalized_actual = normalize_value(actual_value)

            if normalized_expected != normalized_actual:
                errors.append(
                    f"[{key}] {metric_name}: "
                    f"expected {expected_value}, got {actual_value}"
                )

    return len(errors) == 0, errors
