import json
from copy import deepcopy
from pathlib import Path

from app.evaluation.evaluator import compare_multirow_result


ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = ROOT / "evaluation" / "gold_results"


def load_gold(case_id):
    path = GOLD_DIR / f"{case_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_monthly_row_order():
    expected = load_gold("GQ03")
    actual = list(reversed(expected))

    success, errors = compare_multirow_result(
        actual, expected, "month"
    )

    assert success, errors


def test_category_row_order():
    expected = load_gold("GQ04")
    actual = list(reversed(expected))

    success, errors = compare_multirow_result(
        actual, expected, "category"
    )

    assert success, errors


def test_incorrect_revenue():
    expected = load_gold("GQ03")
    actual = deepcopy(expected)

    actual[0]["product_revenue"] = "999999.99"

    success, errors = compare_multirow_result(
        actual, expected, "month"
    )

    assert not success
    assert any("product_revenue" in error for error in errors)


def test_missing_dimension_row():
    expected = load_gold("GQ03")
    actual = deepcopy(expected[1:])

    success, errors = compare_multirow_result(
        actual, expected, "month"
    )

    assert not success
    assert any("Missing dimension keys" in error for error in errors)


def test_duplicate_dimension_key():
    expected = load_gold("GQ04")
    actual = deepcopy(expected)

    actual.append(deepcopy(actual[0]))

    success, errors = compare_multirow_result(
        actual, expected, "category"
    )

    assert not success
    assert any("duplicate dimension key" in error for error in errors)