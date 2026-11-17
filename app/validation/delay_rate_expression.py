
from decimal import Decimal, InvalidOperation

from sqlglot import exp
import sqlglot


NUMERATOR = "delayed_orders"
DENOMINATOR = "delivered_orders_with_delivery_date"


def unwrap(node):
    """Remove parentheses and numeric casts."""
    while isinstance(node, (exp.Paren, exp.Cast)):
        node = node.this
    return node


def is_number(node, expected):
    node = unwrap(node)

    if not isinstance(node, exp.Literal) or node.is_string:
        return False

    try:
        return Decimal(node.this) == Decimal(str(expected))
    except InvalidOperation:
        return False


def is_column(node, name):
    node = unwrap(node)

    return (
        isinstance(node, exp.Column)
        and not node.table
        and node.name.lower() == name
    )


def is_division(node):
    node = unwrap(node)

    if not isinstance(node, exp.Div):
        return False

    return (
        is_column(node.this, NUMERATOR)
        and is_column(node.expression, DENOMINATOR)
    )


def is_scaled_numerator(node):
    node = unwrap(node)

    if not isinstance(node, exp.Mul):
        return False

    left = node.this
    right = node.expression

    return (
        is_column(left, NUMERATOR)
        and is_number(right, 100)
    ) or (
        is_number(left, 100)
        and is_column(right, NUMERATOR)
    )


def is_rate_arithmetic(node):
    node = unwrap(node)

    # (delayed_orders / denominator) * 100
    if isinstance(node, exp.Mul):
        return (
            is_division(node.this)
            and is_number(node.expression, 100)
        ) or (
            is_number(node.this, 100)
            and is_division(node.expression)
        )

    # (100 * delayed_orders) / denominator
    if isinstance(node, exp.Div):
        return (
            is_scaled_numerator(node.this)
            and is_column(node.expression, DENOMINATOR)
        )

    return False


def is_zero_denominator_guard(node):
    node = unwrap(node)

    if not isinstance(node, exp.EQ):
        return False

    return (
        is_column(node.this, DENOMINATOR)
        and is_number(node.expression, 0)
    ) or (
        is_number(node.this, 0)
        and is_column(node.expression, DENOMINATOR)
    )


def is_safe_case_rate(node):
    node = unwrap(node)

    if not isinstance(node, exp.Case):
        return False

    branches = node.args.get("ifs") or []

    if len(branches) != 1:
        return False

    branch = branches[0]

    return (
        is_zero_denominator_guard(branch.this)
        and is_number(branch.args.get("true"), 0)
        and is_rate_arithmetic(node.args.get("default"))
    )


def is_nullif_denominator(node):
    """
    Accept exactly:
        NULLIF(delivered_orders_with_delivery_date, 0)

    Numeric casts and outer parentheses are allowed.
    """

    node = unwrap(node)

    expected = sqlglot.parse_one(
        "SELECT NULLIF("
        "delivered_orders_with_delivery_date, 0)",
        read="postgres",
    ).expressions[0]

    return node == expected


def is_nullif_rate_arithmetic(node):
    """
    Accept:
        (100 * delayed_orders)
        / NULLIF(delivered_orders_with_delivery_date, 0)

    Reject reversed numerator/denominator,
    missing percentage conversion, and unsafe denominators.
    """

    node = unwrap(node)

    if not isinstance(node, exp.Div):
        return False

    return (
        is_scaled_numerator(node.this)
        and is_nullif_denominator(node.expression)
    )




def validate_delay_rate_expression(expression):
    """
    Validate restricted delivery delay rate expressions.

    Supported:
    1. ROUND(CASE WHEN ... END, 2)
    2. ROUND(100 * numerator / NULLIF(denominator, 0), 2)
    3. COALESCE(
           ROUND(100 * numerator / NULLIF(denominator, 0), 2),
           0
       )

    Unknown forms are rejected.
    """

    node = unwrap(expression)

    # Optional COALESCE wrapper
    if isinstance(node, exp.Coalesce):
        fallbacks = node.expressions

        # Accept exactly one fallback, and it must be zero.
        if len(fallbacks) != 1:
            return False

        if not is_number(fallbacks[0], 0):
            return False

        node = unwrap(node.this)

        # COALESCE is only allowed around a NULLIF-based rate.
        if not isinstance(node, exp.Round):
            return False

        if not is_number(node.args.get("decimals"), 2):
            return False

        return is_nullif_rate_arithmetic(
            unwrap(node.this)
        )

    # Existing ROUND-based validation
    if not isinstance(node, exp.Round):
        return False

    if not is_number(node.args.get("decimals"), 2):
        return False

    inner = unwrap(node.this)

    if is_safe_case_rate(inner):
        return True

    if is_nullif_rate_arithmetic(inner):
        return True

    return False

