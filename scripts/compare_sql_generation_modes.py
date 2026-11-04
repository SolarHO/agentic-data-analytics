
import argparse
import csv
from pathlib import Path
from time import perf_counter

from app.agents.sql_generator import build_sql_prompt, llm
from app.agents.sql_validator import validate_sql
from app.agents.sql_executor import execute_sql
from app.context.metric_registry import METRIC_REGISTRY
from app.evaluation.cases import EVALUATION_CASES
from app.evaluation.evaluator import (
    compare_result,
    compare_multirow_result,
)
from app.graph.metric_plan import MetricDefinition, MetricPlan


# Gold Query별 고정 Metric Plan.
# Metric Planner의 LLM 호출 및 변동성을 제거한다.
GOLD_PLANS = {
    "GQ01": {
        "metrics": [
            "delivered_orders",
            "sold_items",
            "product_revenue",
            "freight_revenue",
            "gross_item_value",
        ],
        "dimensions": [],
        "filters": ["order_status = 'delivered'"],
    },
    "GQ02": {
        "metrics": ["average_order_value"],
        "dimensions": [],
        "filters": [],
    },
    "GQ03": {
        "metrics": ["delivered_orders", "product_revenue"],
        "dimensions": ["month"],
        "filters": ["order_status = 'delivered'"],
    },
    "GQ04": {
        "metrics": [
            "delivered_orders",
            "sold_items",
            "product_revenue",
        ],
        "dimensions": ["category"],
        "filters": ["order_status = 'delivered'"],
    },
    "GQ05": {
        "metrics": [
            "delivered_orders_with_delivery_date",
            "delayed_orders",
            "delay_rate_pct",
        ],
        "dimensions": [],
        "filters": [
            "order_status = 'delivered'",
            "order_delivered_customer_date IS NOT NULL",
        ],
    },
    "GQ06": {
        "metrics": [
            "reviews",
            "avg_review_score",
            "negative_reviews",
            "positive_reviews",
        ],
        "dimensions": [],
        "filters": [],
    },
}


def make_plan(case_id):
    definition = GOLD_PLANS[case_id]

    return MetricPlan(
        intent=(
            "trend"
            if "month" in definition["dimensions"]
            else "comparison"
            if "category" in definition["dimensions"]
            else "aggregation"
        ),
        metrics=[
            MetricDefinition(
                name=name,
                description=METRIC_REGISTRY[name]["description"],
            )
            for name in definition["metrics"]
        ],
        dimensions=definition["dimensions"],
        filters=definition["filters"],
    )


def get_token_usage(response):
    usage = getattr(response, "usage_metadata", None) or {}

    if usage:
        return (
            usage.get("input_tokens"),
            usage.get("output_tokens"),
        )

    metadata = getattr(response, "response_metadata", {}) or {}
    token_usage = metadata.get("token_usage", {})

    return (
        token_usage.get("prompt_tokens"),
        token_usage.get("completion_tokens"),
    )


def evaluate_one(case, mode):
    case_id = case["id"]
    question = case["question"]
    plan = make_plan(case_id)

    record = {
        "case_id": case_id,
        "mode": mode,
        "status": "ERROR",
        "prompt_chars": 0,
        "input_tokens": None,
        "output_tokens": None,
        "retrieval_seconds": 0.0,
        "llm_seconds": 0.0,
        "total_seconds": 0.0,
        "error": "",
        "generated_sql": "",
    }

    start = perf_counter()

    try:
        # 1. Context 생성
        t0 = perf_counter()
        prompt = build_sql_prompt(
            question=question,
            metric_plan=plan,
            mode=mode,
        )

        record["retrieval_seconds"] = perf_counter() - t0
        record["prompt_chars"] = len(prompt)

        # 2. 실제 LLM 호출
        t1 = perf_counter()
        response = llm.invoke([
            ("system", prompt),
            ("human", question),
        ])

        record["llm_seconds"] = perf_counter() - t1

        input_tokens, output_tokens = get_token_usage(response)
        record["input_tokens"] = input_tokens
        record["output_tokens"] = output_tokens

        sql = str(response.content).strip()
        record["generated_sql"] = sql

        # 3. 기존 SQL Validator
        validation = validate_sql({"sql": sql})

        if not validation.get("sql_valid"):
            record["status"] = "VALIDATION_FAIL"
            record["error"] = str(
                validation.get("validation_error")
            )
            return record

        # 4. 기존 SQL Executor
        execution = execute_sql({
            "sql": sql,
            "sql_valid": True,
        })

        if execution.get("execution_error"):
            record["status"] = "EXECUTION_FAIL"
            record["error"] = str(
                execution["execution_error"]
            )
            return record

        # 5. Gold Query 결과 비교
        actual = execution.get("result", [])

        if case["evaluation_type"] == "multi":
            passed, errors = compare_multirow_result(
                actual=actual,
                expected=case["expected"],
                dimension=case["dimension"],
            )
        else:
            passed, errors = compare_result(
                actual=actual,
                expected=case["expected"],
            )

        record["status"] = "PASS" if passed else "GOLD_FAIL"
        record["error"] = "; ".join(errors)

    except Exception as exc:
        record["status"] = "ERROR"
        record["error"] = f"{type(exc).__name__}: {exc}"

    finally:
        record["total_seconds"] = perf_counter() - start

    return record


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case",
        default="GQ02",
        choices=sorted(GOLD_PLANS),
        help="Single Gold Query to evaluate (default: GQ02)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all six Gold Queries",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["full", "registry", "hybrid"],
        choices=["full", "registry", "hybrid"],
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional CSV output path",
    )

    args = parser.parse_args()

    selected_cases = [
        case
        for case in EVALUATION_CASES
        if args.all or case["id"] == args.case
    ]

    # 평가 설정 자체가 잘못되면 LLM 호출 전 종료한다.
    if set(GOLD_PLANS) != {
        case["id"] for case in EVALUATION_CASES
    }:
        raise RuntimeError("Gold plan definitions are incomplete.")

    for case in selected_cases:
        plan = make_plan(case["id"])
        expected_metrics = (
            set(case["expected"][0]) - {case["dimension"]}
            if case["evaluation_type"] == "multi"
            else set(case["expected"])
        )
        planned_metrics = {m.name for m in plan.metrics}

        if expected_metrics != planned_metrics:
            raise RuntimeError(
                f"{case['id']}: Metric Plan does not match Gold columns."
            )

    records = []

    for case in selected_cases:
        for mode in args.modes:
            print(f"\n[{case['id']}] {mode.upper()}")

            result = evaluate_one(case, mode)
            records.append(result)

            print("Status:", result["status"])
            print("Prompt chars:", result["prompt_chars"])
            print("Input tokens:", result["input_tokens"])
            print("Output tokens:", result["output_tokens"])
            print(
                "Retrieval seconds:",
                round(result["retrieval_seconds"], 3),
            )
            print(
                "LLM seconds:",
                round(result["llm_seconds"], 3),
            )
            print(
                "Total seconds:",
                round(result["total_seconds"], 3),
            )

            if result["error"]:
                print("Error:", result["error"][:400])
            if result["status"] in {
                "GOLD_FAIL",
                "VALIDATION_FAIL",
                "EXECUTION_FAIL",
            }:
                print("\nGenerated SQL:")
                print(result["generated_sql"])

    print("\n=== Comparison Summary ===")
    for mode in args.modes:
        subset = [r for r in records if r["mode"] == mode]
        passes = sum(r["status"] == "PASS" for r in subset)

        print(f"{mode}: {passes}/{len(subset)} PASS")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(records[0]),
            )
            writer.writeheader()
            writer.writerows(records)

        print("Results saved:", output_path)


if __name__ == "__main__":
    main()
