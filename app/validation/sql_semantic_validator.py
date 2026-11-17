
import sqlglot
from sqlglot import exp

from app.graph.metric_plan import MetricPlan, MetricDefinition
from app.validation.metric_policy import (
    resolve_metric_policies,
)
from app.validation.delay_rate_expression import (
    validate_delay_rate_expression,
)
from app.context.metric_registry import METRIC_REGISTRY

SUPPORTED_METRICS = {
    "delivered_orders_with_delivery_date",
    "delayed_orders",
}


def flatten_and(expression):
    if expression is None:
        return []

    if isinstance(expression, exp.And):
        return (
            flatten_and(expression.this)
            + flatten_and(expression.expression)
        )

    return [expression]


def is_status_delivered(node):
    if not isinstance(node, exp.EQ):
        return False

    left, right = node.this, node.expression

    for column, value in [(left, right), (right, left)]:
        if (
            isinstance(column, exp.Column)
            and column.name.lower() == "order_status"
            and isinstance(value, exp.Literal)
            and value.is_string
            and value.this.lower() == "delivered"
        ):
            return True

    return False



def is_actual_date_not_null(node):
    """
    Check whether a predicate is exactly equivalent to:
    order_delivered_customer_date IS NOT NULL
    """

    expected = sqlglot.parse_one(
        "SELECT 1 "
        "WHERE order_delivered_customer_date IS NOT NULL",
        read="postgres",
    ).args["where"].this

    # Remove parentheses wrapping the entire predicate.
    while isinstance(node, exp.Paren):
        node = node.this

    actual = node.copy()

    # Accept orders.column and aliases such as o.column.
    # The validator currently supports only the orders table.
    for column in actual.find_all(exp.Column):
        column.set("table", None)
        column.set("db", None)
        column.set("catalog", None)

    return actual == expected



def is_delayed_condition(node):
    return (
        isinstance(node, exp.GT)
        and isinstance(node.this, exp.Column)
        and isinstance(node.expression, exp.Column)
        and node.this.name.lower()
        == "order_delivered_customer_date"
        and node.expression.name.lower()
        == "order_estimated_delivery_date"
    )



def is_supported_count(node):
    """
    Only COUNT(*) is supported.

    Reject:
    - COUNT(column)
    - COUNT(DISTINCT column)
    - Other COUNT expressions
    """

    if not isinstance(node, exp.Count):
        return False

    # COUNT(DISTINCT ...) has a Distinct AST node.
    if isinstance(node.this, exp.Distinct):
        return False

    return (
        isinstance(node.this, exp.Star)
        and not node.args.get("distinct")
    )


def get_aggregate_predicates(expression):
    """
    Supported:
    - COUNT(*)
    - COUNT(*) FILTER (WHERE ...)

    Returns:
    - list of predicates for supported counts
    - None for unsupported aggregates
    """

    # COUNT(*) FILTER (WHERE ...)
    if isinstance(expression, exp.Filter):

        count_node = expression.this

        if not is_supported_count(count_node):
            return None

        where = expression.args.get("expression")

        if not isinstance(where, exp.Where):
            return None

        return flatten_and(where.this)

    # COUNT(*) without FILTER
    if is_supported_count(expression):
        return []

    return None



def resolve_aggregation_select(tree, selected_metrics):
    """
    Resolve the SELECT that computes metric aggregates.

    Supported:
    1. Direct SELECT FROM orders
    2. One CTE containing aggregates, followed by
       direct column projections from that CTE.

    No joins, grouping, nested queries, or transformations.
    """

    with_clause = tree.args.get("with_")

    # Existing direct SELECT behavior
    if with_clause is None:
        if len(list(tree.find_all(exp.Select))) != 1:
            raise ValueError("Nested queries are not supported.")

        return tree

    # Restrict CTE support to one simple aggregation CTE.
    ctes = with_clause.expressions

    if len(ctes) != 1:
        raise ValueError("Exactly one CTE is supported.")

    cte = ctes[0]
    cte_name = cte.alias_or_name

    source = cte.this

    if not isinstance(source, exp.Select):
        raise ValueError("CTE must contain a SELECT.")

    if len(list(tree.find_all(exp.Select))) != 2:
        raise ValueError("Nested queries are not supported.")

    # Outer SELECT must read directly from the CTE.
    outer_from = tree.args.get("from_")

    if outer_from is None:
        raise ValueError("Missing outer FROM.")

    outer_table = outer_from.this

    if (
        not isinstance(outer_table, exp.Table)
        or outer_table.name.lower() != cte_name.lower()
    ):
        raise ValueError("Outer SELECT must read from the CTE.")

    # Only direct projections are supported.
    # No additional filtering, grouping, or joins.
    for key in (
        "where",
        "group",
        "having",
        "joins",
        "distinct",
        "limit",
        "qualify",
    ):
        if tree.args.get(key):
            raise ValueError(
                f"Unsupported outer SELECT clause: {key}"
            )

    outer_columns = {}

    for projection in tree.expressions:
        output_name = projection.alias_or_name

        expression = (
            projection.this
            if isinstance(projection, exp.Alias)
            else projection
        )

        if not isinstance(expression, exp.Column):
            raise ValueError(
                "Outer SELECT must project CTE columns directly."
            )

        if expression.table and (
            expression.table.lower() != cte_name.lower()
        ):
            raise ValueError("Invalid CTE column qualifier.")

        outer_columns[output_name] = expression.name

    if set(outer_columns) != selected_metrics:
        raise ValueError(
            "Outer columns must match selected metrics."
        )

    for output_name, source_name in outer_columns.items():
        if output_name != source_name:
            raise ValueError(
                "Metric renaming is not supported."
            )

    source_columns = {
        projection.alias_or_name
        for projection in source.expressions
    }

    if not selected_metrics <= source_columns:
        raise ValueError(
            "CTE does not provide all required metrics."
        )

    return source


GQ05_METRICS = {
    "delivered_orders_with_delivery_date",
    "delayed_orders",
    "delay_rate_pct",
}

GQ05_COUNT_METRICS = GQ05_METRICS - {"delay_rate_pct"}



def resolve_gq05_count_source(with_clause):
    """
    Resolve supported GQ05 CTE structures.

    1 CTE:
        counts -> orders

    2 CTEs:
        delivered -> orders
        counts -> delivered

    The second form is normalized to a SELECT
    directly aggregating orders, so the existing
    population validator can be reused.
    """

    if with_clause is None:
        raise ValueError("One or two CTEs are required.")

    if with_clause.args.get("recursive"):
        raise ValueError("Recursive CTEs are not supported.")

    ctes = with_clause.expressions

    if len(ctes) == 1:
        count_cte = ctes[0]

        if not isinstance(count_cte.this, exp.Select):
            raise ValueError("COUNT CTE must contain a SELECT.")

        return (
            count_cte.alias_or_name.lower(),
            count_cte.this,
            count_cte.this,
        )

    if len(ctes) != 2:
        raise ValueError("Only one or two CTEs are supported.")

    population_cte, count_cte = ctes

    population_name = population_cte.alias_or_name.lower()
    count_name = count_cte.alias_or_name.lower()

    if not population_name or not count_name:
        raise ValueError("CTE names are required.")

    if population_name == count_name:
        raise ValueError("Duplicate CTE names.")

    population = population_cte.this
    counts = count_cte.this

    if not (
        isinstance(population, exp.Select)
        and isinstance(counts, exp.Select)
    ):
        raise ValueError("Both CTEs must contain SELECT.")

    # Population CTE must be a simple projection
    # with a WHERE clause. Reject other operations.
    allowed_population_args = {
        "expressions",
        "from_",
        "where",
    }

    for key, value in population.args.items():
        if key not in allowed_population_args and value:
            raise ValueError(
                f"Unsupported population CTE clause: {key}"
            )

    required_columns = {
        "order_id",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    }

    columns = population.expressions

    if (
        len(columns) != len(required_columns)
        or not all(isinstance(c, exp.Column) for c in columns)
        or any(c.table for c in columns)
        or {c.name.lower() for c in columns} != required_columns
    ):
        raise ValueError(
            "Population CTE must project the three "
            "required order columns directly."
        )

    population_from = population.args.get("from_")

    if population_from is None:
        raise ValueError("Population CTE missing FROM.")

    base_table = population_from.this

    if (
        not isinstance(base_table, exp.Table)
        or base_table.name.lower() != "orders"
        or base_table.args.get("alias")
        or base_table.args.get("db")
        or base_table.args.get("catalog")
    ):
        raise ValueError(
            "Population CTE must read directly from orders."
        )

    population_where = population.args.get("where")

    if population_where is None:
        raise ValueError(
            "Population CTE must define population conditions."
        )

    counts_from = counts.args.get("from_")

    if counts_from is None:
        raise ValueError("COUNT CTE missing FROM.")

    counts_table = counts_from.this

    if (
        not isinstance(counts_table, exp.Table)
        or counts_table.name.lower() != population_name
        or counts_table.args.get("alias")
    ):
        raise ValueError(
            "COUNT CTE must read directly from population CTE."
        )

    # Prevent stale CTE qualifiers after normalization.
    if any(c.table for c in counts.find_all(exp.Column)):
        raise ValueError(
            "Qualified COUNT CTE columns are not supported."
        )

    # Build a copy, never mutate the original query.
    normalized = counts.copy()

    normalized.set(
        "from_",
        population_from.copy(),
    )

    counts_where = counts.args.get("where")

    if counts_where is None:
        combined_where = population_where.copy()
    else:
        combined_where = exp.Where(
            this=exp.and_(
                population_where.this.copy(),
                counts_where.this.copy(),
            )
        )

    normalized.set("where", combined_where)

    return count_name, counts, normalized



def validate_gq05_cte(sql, metric_plan):
    """
    Validate a restricted GQ05 CTE structure:
    - One CTE with two validated COUNT metrics
    - One outer SELECT with two direct count columns
    - One validated delay_rate_pct expression
    """

    tree = sqlglot.parse_one(sql, read="postgres")

    if not isinstance(tree, exp.Select):
        raise ValueError("Only SELECT is supported.")

    with_clause = tree.args.get("with_")

    cte_name, source, count_source = (
        resolve_gq05_count_source(with_clause)
    )

    expected_selects = (
        len(with_clause.expressions) + 1
    )

    if len(list(tree.find_all(exp.Select))) != expected_selects:
        raise ValueError(
            "Nested queries are not supported."
        )

    outer_from = tree.args.get("from_")

    if (
        outer_from is None
        or not isinstance(outer_from.this, exp.Table)
        or outer_from.this.name.lower() != cte_name
    ):
        raise ValueError("Outer SELECT must read from the CTE.")

    # Reject outer operations that could change the metrics.
    for key in (
        "where",
        "group",
        "having",
        "joins",
        "distinct",
        "limit",
        "offset",
        "qualify",
        "order",
    ):
        if tree.args.get(key):
            raise ValueError(
                f"Unsupported outer clause: {key}"
            )

    # The CTE must produce exactly the two count metrics.
    source_columns = [
        projection.alias_or_name
        for projection in source.expressions
    ]

    if (
        len(source_columns) != 2
        or set(source_columns) != GQ05_COUNT_METRICS
    ):
        raise ValueError(
            "CTE must produce exactly the two count metrics."
        )

    
    # Always validate both canonical count metrics,
    # regardless of which final outputs were requested.
    count_plan = MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=name,
                description=METRIC_REGISTRY[name]["description"],
            )
            for name in sorted(GQ05_COUNT_METRICS)
        ],
        filters=[],
        dimensions=[],
    )

    count_result = validate_metric_semantics(
        count_source.sql(dialect="postgres"),
        count_plan,
    )

    if not count_result["semantic_valid"]:
        raise ValueError(count_result["semantic_error"])

    # Validate the outer projection and rate expression.
    
    projections = {}

    for projection in tree.expressions:

        # Explicit alias: expression AS metric_name
        if isinstance(projection, exp.Alias):
            name = projection.alias
            expression = projection.this

        # Direct column reference without alias
        elif isinstance(projection, exp.Column):
            name = projection.name
            expression = projection

        else:
            raise ValueError(
                "Computed expressions must have an alias."
            )

        if name in projections:
            raise ValueError(
                f"Duplicate output alias: {name}"
            )

        projections[name] = expression


    requested_metrics = {
        metric.name
        for metric in metric_plan.metrics
    }

    if set(projections) != requested_metrics:
        raise ValueError(
            "Outer output columns do not match requested metrics."
        )

    for name in GQ05_COUNT_METRICS & requested_metrics:
        node = projections[name]

        if not isinstance(node, exp.Column):
            raise ValueError(
                f"{name}: direct CTE column required"
            )

        if node.name != name:
            raise ValueError(
                f"{name}: incorrect source column"
            )

        if node.table and node.table.lower() != cte_name:
            raise ValueError(
                f"{name}: invalid CTE qualifier"
            )

    rate_expression = projections["delay_rate_pct"]

    if not validate_delay_rate_expression(rate_expression):
        raise ValueError(
            "delay_rate_pct: invalid calculation formula"
        )

    return {
        "semantic_valid": True,
        "semantic_error": None,
    }


def classify_delivery_predicate(node):
    """
    Recognize the three canonical GQ05 predicates.
    """

    while isinstance(node, exp.Paren):
        node = node.this

    if is_status_delivered(node):
        return "delivered_status"

    if is_actual_date_not_null(node):
        return "actual_date_not_null"

    if is_delayed_condition(node):
        return "delayed_condition"

    return None


def validate_delivery_predicates(
    metric_name,
    predicates,
):
    """
    Require exactly the approved predicates for each metric.
    Extra or duplicate predicates are rejected.
    """

    expected = {
        "delivered_status",
        "actual_date_not_null",
    }

    if metric_name == "delayed_orders":
        expected.add("delayed_condition")

    classified = [
        classify_delivery_predicate(predicate)
        for predicate in predicates
    ]

    if (
        None in classified
        or len(classified) != len(expected)
        or set(classified) != expected
    ):
        raise ValueError(
            f"{metric_name}: invalid or extra "
            "population conditions"
        )


def validate_metric_semantics(
    sql: str,
    metric_plan: MetricPlan,
) -> dict:
    """
    Conservative population checks for simple delivery counts.

    This is NOT a general SQL equivalence checker.
    """

    policies = resolve_metric_policies(metric_plan)

    selected = set(policies)

    
    if "delay_rate_pct" in selected:
        # Rate validation supports a subset of the
        # canonical delivery metrics as final outputs.
        if not selected <= GQ05_METRICS:
            return {
                "semantic_valid": False,
                "semantic_error": (
                    "Unsupported metrics for this semantic "
                    "validator version."
                ),
            }

        try:
            return validate_gq05_cte(sql, metric_plan)

        except (ValueError, sqlglot.errors.SqlglotError) as exc:
            return {
                "semantic_valid": False,
                "semantic_error": str(exc),
            }


    if not selected <= SUPPORTED_METRICS:
        return {
            "semantic_valid": False,
            "semantic_error": (
                "Unsupported metrics for this semantic "
                "validator version."
            ),
        }

    try:
        statements = sqlglot.parse(sql, read="postgres")

        if len(statements) != 1:
            raise ValueError("Expected exactly one statement.")

        tree = statements[0]

        if not isinstance(tree, exp.Select):
            raise ValueError("Only SELECT is supported.")

        # if len(list(tree.find_all(exp.Select))) != 1:
        #     raise ValueError(
        #         "Nested queries and CTEs are not supported."
        #     )

        # if tree.args.get("with_") is not None:
        #     raise ValueError("CTEs are not supported.")
        source_select = resolve_aggregation_select(
            tree,
            selected,
        )

        tables = list(source_select.find_all(exp.Table))

        if (
            len(tables) != 1
            or tables[0].name.lower() != "orders"
            or source_select.find(exp.Join) is not None
        ):
            raise ValueError(
                "Only single-table orders queries are supported."
            )

        # Disallow unsupported aggregation modifiers.
        for key in (
            "group",
            "having",
            "distinct",
            "limit",
            "qualify",
        ):
            if source_select.args.get(key):
                raise ValueError(
                    f"Unsupported aggregation clause: {key}"
                )

        global_where = source_select.args.get("where")

        global_predicates = flatten_and(
            global_where.this if global_where else None
        )

        projections = {}

        for expression in source_select.expressions:
            if not isinstance(expression, exp.Alias):
                continue

            projections[expression.alias] = expression.this

        for metric_name in selected:
            expression = projections.get(metric_name)

            if expression is None:
                raise ValueError(
                    f"Missing metric column: {metric_name}"
                )

            aggregate_predicates = get_aggregate_predicates(
                expression
            )

            if aggregate_predicates is None:
                raise ValueError(
                    f"Unsupported aggregate: {metric_name}"
                )

            
            predicates = (
                global_predicates + aggregate_predicates
            )

            # 1. Mandatory delivered status
            if not any(
                is_status_delivered(p)
                for p in predicates
            ):
                raise ValueError(
                    f"{metric_name}: delivered status missing"
                )

            # 2. Mandatory actual delivery date
            if not any(
                is_actual_date_not_null(p)
                for p in predicates
            ):
                raise ValueError(
                    f"{metric_name}: actual delivery date "
                    "null check missing"
                )

            # 3. Delay comparison for delayed_orders
            if metric_name == "delayed_orders":
                if not any(
                    is_delayed_condition(p)
                    for p in predicates
                ):
                    raise ValueError(
                        "delayed_orders: delay comparison missing"
                    )

            # 4. Reject unknown, extra or duplicate filters
            validate_delivery_predicates(
                metric_name,
                predicates,
            )

            if not any(
                is_status_delivered(p)
                for p in predicates
            ):
                raise ValueError(
                    f"{metric_name}: delivered status missing"
                )

            if not any(
                is_actual_date_not_null(p)
                for p in predicates
            ):
                raise ValueError(
                    f"{metric_name}: actual delivery date "
                    "null check missing"
                )

            if metric_name == "delayed_orders":
                if not any(
                    is_delayed_condition(p)
                    for p in predicates
                ):
                    raise ValueError(
                        "delayed_orders: delay comparison missing"
                    )

        return {
            "semantic_valid": True,
            "semantic_error": None,
        }

    except (ValueError, sqlglot.errors.SqlglotError) as exc:
        return {
            "semantic_valid": False,
            "semantic_error": str(exc),
        }
