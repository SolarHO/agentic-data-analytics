
from statistics import mean

from app.rag.retriever import search_context


EVALUATION_CASES = [
    {
        "question": "배송 지연율을 계산하려면 어떤 테이블이 필요해?",
        "relevant_ids": {
            "business_rule:5",
            "metric:delay_rate_pct",
            "metric:delayed_orders",
            "schema:orders",
        },
        "required_ids": {
            "business_rule:5",
            "schema:orders",
        },
    },
    {
        "question": "평균 주문 금액은 어떻게 계산해야 해?",
        "relevant_ids": {
            "business_rule:4",
            "metric:average_order_value",
            "schema:orders",
            "schema:order_items",
        },
        "required_ids": {
            "business_rule:4",
            "schema:order_items",
        },
    },
    {
        "question": "상품 카테고리별 매출을 분석하고 싶어.",
        "relevant_ids": {
            "dimension:category",
            "business_rule:7",
            "metric:product_revenue",
            "schema:products",
            "schema:category_translation",
        },
        "required_ids": {
            "dimension:category",
            "schema:products",
        },
    },
    {
        "question": "월별 주문 수와 매출 추이를 알고 싶어.",
        "relevant_ids": {
            "dimension:month",
            "metric:delivered_orders",
            "metric:product_revenue",
            "schema:orders",
        },
        "required_ids": {
            "dimension:month",
            "schema:orders",
        },
    },
    {
        "question": "긍정 리뷰와 부정 리뷰를 어떻게 구분해?",
        "relevant_ids": {
            "business_rule:6",
            "metric:negative_reviews",
            "metric:positive_reviews",
            "schema:order_reviews",
        },
        "required_ids": {
            "business_rule:6",
            "schema:order_reviews",
        },
    },
]


def evaluate_retrieval(top_k=5):
    hits = []
    recalls = []
    reciprocal_ranks = []
    required_coverages = []

    for case in EVALUATION_CASES:
        results = search_context(
            question=case["question"],
            top_k=top_k,
        )

        retrieved_ids = [
            result["document_id"]
            for result in results
        ]
        retrieved_set = set(retrieved_ids)

        relevant_ids = case["relevant_ids"]
        required_ids = case["required_ids"]

        matched = retrieved_set & relevant_ids
        missing_required = required_ids - retrieved_set

        hit = int(bool(matched))
        recall = len(matched) / len(relevant_ids)

        reciprocal_rank = 0.0
        for rank, document_id in enumerate(
            retrieved_ids,
            start=1,
        ):
            if document_id in relevant_ids:
                reciprocal_rank = 1 / rank
                break

        required_coverage = int(
            not missing_required
        )

        hits.append(hit)
        recalls.append(recall)
        reciprocal_ranks.append(reciprocal_rank)
        required_coverages.append(required_coverage)

        print("=" * 65)
        print(f"Question: {case['question']}")
        print(f"Retrieved: {retrieved_ids}")
        print(f"Matched: {sorted(matched)}")
        print(f"Missing required: {sorted(missing_required)}")
        print(f"Recall@{top_k}: {recall:.3f}")
        print(f"RR@{top_k}: {reciprocal_rank:.3f}")

    print("\n=== Retrieval Evaluation ===")
    print(f"Questions: {len(EVALUATION_CASES)}")
    print(f"Hit@{top_k}: {mean(hits):.2%}")
    print(f"Mean Recall@{top_k}: {mean(recalls):.2%}")
    print(f"MRR@{top_k}: {mean(reciprocal_ranks):.3f}")
    print(
        f"Required Coverage@{top_k}: "
        f"{mean(required_coverages):.2%}"
    )


if __name__ == "__main__":
    evaluate_retrieval(top_k=5)
