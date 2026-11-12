
import csv
from pathlib import Path

from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)
from app.validation.sql_semantic_validator import (
    validate_metric_semantics,
)


CSV_PATH = Path("evaluation/gq05_population_rules.csv")


def make_plan():
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=name,
                description=name,
            )
            for name in [
                "delivered_orders_with_delivery_date",
                "delayed_orders",
                "delay_rate_pct",
            ]
        ],
        dimensions=[],
        filters=[],
    )


def main():
    with CSV_PATH.open(
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if "generated_sql" not in (
            reader.fieldnames or []
        ):
            raise ValueError(
                "CSV does not contain generated_sql. "
                "SQL replay is unavailable."
            )

        rows = list(reader)

    plan = make_plan()

    for row in rows:
        mode = row["mode"]
        sql = row["generated_sql"]

        if not sql.strip():
            print(f"[{mode}] SKIP: SQL is empty")
            continue

        result = validate_metric_semantics(
            sql=sql,
            metric_plan=plan,
        )

        print("=" * 60)
        print("Mode:", mode)
        print("Previous Gold status:", row["status"])
        print("Semantic valid:", result["semantic_valid"])
        print("Semantic error:", result["semantic_error"])


if __name__ == "__main__":
    main()
