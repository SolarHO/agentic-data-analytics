
import pytest
import sqlglot

from sqlglot import exp

from app.validation.delay_rate_expression import (
    validate_delay_rate_expression,
)


def extract_expression(sql):
    tree = sqlglot.parse_one(sql, read="postgres")
    projection = tree.expressions[0]

    assert isinstance(projection, exp.Alias)
    return projection.this


def make_sql(formula):
    return (
        "SELECT "
        + formula
        + " AS delay_rate_pct FROM stats"
    )


VALID_FORMULA = """
ROUND(
    CASE
        WHEN delivered_orders_with_delivery_date = 0
        THEN 0
        ELSE
            100.0 * delayed_orders
            / delivered_orders_with_delivery_date
    END,
    2
)
"""


@pytest.mark.parametrize(
    "formula",
    [
        VALID_FORMULA,
        """
        ROUND(
            CASE
                WHEN delivered_orders_with_delivery_date = 0
                THEN 0
                ELSE (
                    delayed_orders::numeric
                    / delivered_orders_with_delivery_date::numeric
                ) * 100
            END,
            2
        )
        """,
    ],
)
def test_valid_delay_rate_formula(formula):
    expression = extract_expression(make_sql(formula))

    assert validate_delay_rate_expression(expression) is True


@pytest.mark.parametrize(
    "formula",
    [
        # Numerator and denominator are reversed.
        """
        ROUND(
            CASE WHEN delivered_orders_with_delivery_date = 0
            THEN 0
            ELSE
                100.0 * delivered_orders_with_delivery_date
                / delayed_orders
            END,
            2
        )
        """,

        # Missing percentage conversion.
        """
        ROUND(
            CASE WHEN delivered_orders_with_delivery_date = 0
            THEN 0
            ELSE
                delayed_orders
                / delivered_orders_with_delivery_date
            END,
            2
        )
        """,

        # Incorrect rounding precision.
        """
        ROUND(
            CASE WHEN delivered_orders_with_delivery_date = 0
            THEN 0
            ELSE
                100 * delayed_orders
                / delivered_orders_with_delivery_date
            END,
            1
        )
        """,

        # Missing zero-denominator guard.
        """
        ROUND(
            100 * delayed_orders
            / delivered_orders_with_delivery_date,
            2
        )
        """,

        # Constant result that ignores the counts.
        "ROUND(8.11, 2)",
    ],
)
def test_invalid_delay_rate_formula(formula):
    expression = extract_expression(make_sql(formula))

    assert validate_delay_rate_expression(expression) is False


@pytest.mark.parametrize(
    "formula",
    [
        """
        ROUND(
            100.0 * delayed_orders::numeric
            / NULLIF(delivered_orders_with_delivery_date, 0),
            2
        )
        """,
        """
        ROUND(
            100 * delayed_orders::numeric
            / NULLIF(
                delivered_orders_with_delivery_date, 0
            )::numeric,
            2
        )
        """,
    ],
)
def test_valid_nullif_rate_formula(formula):
    expression = extract_expression(make_sql(formula))

    assert validate_delay_rate_expression(expression) is True


@pytest.mark.parametrize(
    "formula",
    [
        # Numerator and denominator reversed
        """
        ROUND(
            100 * delivered_orders_with_delivery_date
            / NULLIF(delayed_orders, 0),
            2
        )
        """,

        # Missing percentage conversion
        """
        ROUND(
            delayed_orders
            / NULLIF(delivered_orders_with_delivery_date, 0),
            2
        )
        """,

        # Incorrect denominator
        """
        ROUND(
            100 * delayed_orders
            / NULLIF(delayed_orders, 0),
            2
        )
        """,

        # Incorrect rounding precision
        """
        ROUND(
            100 * delayed_orders
            / NULLIF(delivered_orders_with_delivery_date, 0),
            1
        )
        """,

        # Missing divide-by-zero protection
        """
        ROUND(
            100 * delayed_orders
            / delivered_orders_with_delivery_date,
            2
        )
        """,
    ],
)
def test_invalid_nullif_rate_formula(formula):
    expression = extract_expression(make_sql(formula))

    assert validate_delay_rate_expression(expression) is False

