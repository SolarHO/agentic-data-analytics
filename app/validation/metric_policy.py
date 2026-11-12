
from app.context.metric_registry import METRIC_REGISTRY
from app.graph.metric_plan import MetricPlan


def resolve_metric_policies(
    metric_plan: MetricPlan,
) -> dict[str, dict]:
    """
    Resolve canonical metric policies independently
    of LLM-generated metric descriptions.
    """

    policies = {}

    for metric in metric_plan.metrics:
        name = metric.name

        if name not in METRIC_REGISTRY:
            raise ValueError(f"Unknown metric: {name}")

        definition = METRIC_REGISTRY[name]

        policies[name] = {
            "required_population": list(
                definition.get("required_population", [])
            ),
            "calculation_condition": definition.get(
                "calculation_condition"
            ),
            "formula": definition.get("formula"),
        }

    return policies
