from app.agents.metric_planner import create_metric_plan


def main():
    questions = [
        "평균 주문 금액은 얼마야?",
        "배송 완료된 주문 수와 상품 매출을 알려줘.",
        "월별 상품 매출 추이를 알려줘.",
    ]

    for question in questions:
        print("=" * 60)
        print(f"Question: {question}")

        plan = create_metric_plan(question)

        print("\nMetric Plan:")
        print(plan.model_dump_json(indent=2))

        print()


if __name__ == "__main__":
    main()