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
    expected: dict[str, dict[str, Any]],
) -> tuple[bool, list[str]]:
    """
    Compare a single-row SQL result with the expected Gold result.

    A metric may define multiple acceptable SQL column aliases.
    """
    errors: list[str] = []

    if not actual:
        return False, ["Query returned no rows."]

    if len(actual) != 1:
        return False, [
            f"Expected 1 row, but query returned {len(actual)} rows."
        ]

    actual_row = actual[0]

    for metric_name, metric in expected.items():
        expected_value = metric["value"]
        aliases = metric["aliases"]

        matched_alias = next(
            (
                alias
                for alias in aliases
                if alias in actual_row
            ),
            None,
        )

        if matched_alias is None:
            errors.append(
                f"Missing metric '{metric_name}'. "
                f"Accepted aliases: {aliases}"
            )
            continue

        actual_value = actual_row[matched_alias]

        normalized_actual = normalize_value(actual_value)
        normalized_expected = normalize_value(expected_value)

        if normalized_actual != normalized_expected:
            errors.append(
                f"{metric_name}: expected {expected_value}, "
                f"got {actual_value} "
                f"(column: {matched_alias})"
            )

    return len(errors) == 0, errors