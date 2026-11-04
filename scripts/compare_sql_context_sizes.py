
from app.agents.sql_generator import build_sql_prompt
from app.graph.metric_plan import MetricDefinition, MetricPlan


def main():
    question = "상품 카테고리별 매출을 분석해줘."

    plan = MetricPlan(
        intent="comparison",
        metrics=[
            MetricDefinition(
                name="product_revenue",
                description="Product revenue",
            ),
        ],
        dimensions=["category"],
        filters=[],
    )

    print("=" * 60)
    print("SQL Generator Context Size Comparison")
    print("=" * 60)
    print(f"Question: {question}\n")

    for mode in ("full", "registry", "hybrid"):
        prompt = build_sql_prompt(
            question=question,
            metric_plan=plan,
            mode=mode,
        )

        print(
            f"{mode:10s} | "
            f"prompt_chars={len(prompt):5d}"
        )


if __name__ == "__main__":
    main()
