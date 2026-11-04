
from statistics import mean

from app.graph.metric_plan import (
    MetricDefinition,
    MetricPlan,
)
from app.rag.context_resolver import (
    resolve_required_document_ids,
)
from app.rag.hybrid_retriever import (
    get_documents_by_ids,
    hybrid_search_context,
)
from app.rag.retriever import search_context


TEST_CASES = [
    {
        "question": "배송 지연율을 계산하려면 어떤 테이블이 필요해?",
        "metrics": ["delay_rate_pct"],
        "dimensions": [],
        "gold_required": {
            "business_rule:5",
            "schema:orders",
        },
    },
    {
        "question": "평균 주문 금액은 어떻게 계산해야 해?",
        "metrics": ["average_order_value"],
        "dimensions": [],
        "gold_required": {
            "business_rule:4",
            "schema:order_items",
        },
    },
    {
        "question": "상품 카테고리별 매출을 분석하고 싶어.",
        "metrics": ["product_revenue"],
        "dimensions": ["category"],
        "gold_required": {
            "dimension:category",
            "schema:products",
        },
    },
    {
        "question": "월별 주문 수와 매출 추이를 알고 싶어.",
        "metrics": ["delivered_orders", "product_revenue"],
        "dimensions": ["month"],
        "gold_required": {
            "dimension:month",
            "schema:orders",
        },
    },
    {
        "question": "긍정 리뷰와 부정 리뷰를 어떻게 구분해?",
        "metrics": ["positive_reviews", "negative_reviews"],
        "dimensions": [],
        "gold_required": {
            "business_rule:6",
            "schema:order_reviews",
        },
    },
]


def make_plan(case):
    return MetricPlan(
        intent="aggregation",
        metrics=[
            MetricDefinition(
                name=name,
                description=name,
            )
            for name in case["metrics"]
        ],
        dimensions=case["dimensions"],
        filters=[],
    )


def summarize(documents, gold_required):
    retrieved_ids = {
        doc["document_id"]
        for doc in documents
    }

    matched = retrieved_ids & gold_required

    return {
        "documents": len(documents),
        "characters": sum(
            len(doc["content"])
            for doc in documents
        ),
        "coverage": len(matched) / len(gold_required),
        "all_required": gold_required <= retrieved_ids,
    }


def main():
    methods = [
        "vector",
        "registry",
        "hybrid",
    ]

    summaries = {
        name: []
        for name in methods
    }

    for case in TEST_CASES:
        question = case["question"]
        plan = make_plan(case)

        required_ids = resolve_required_document_ids(
            plan
        )

        vector_docs = search_context(
            question=question,
            top_k=5,
        )

        registry_docs = get_documents_by_ids(
            required_ids
        )

        registry_found = {
            doc["document_id"]
            for doc in registry_docs
        }

        if required_ids - registry_found:
            raise RuntimeError(
                "Registry documents missing: "
                f"{sorted(required_ids - registry_found)}"
            )

        hybrid_docs = hybrid_search_context(
            question=question,
            metric_plan=plan,
            vector_top_k=5,
            max_documents=15,
        )

        results = {
            "vector": vector_docs,
            "registry": registry_docs,
            "hybrid": hybrid_docs,
        }

        print("=" * 72)
        print("Question:", question)

        for name, documents in results.items():
            score = summarize(
                documents,
                case["gold_required"],
            )

            summaries[name].append(score)

            print(
                f"{name:8s} | "
                f"docs={score['documents']:2d} | "
                f"chars={score['characters']:5d} | "
                f"coverage={score['coverage']:.0%} | "
                f"all_required={score['all_required']}"
            )

        print()

    print("\n=== Retrieval Comparison Summary ===")

    for name in methods:
        scores = summaries[name]

        avg_docs = mean(
            score["documents"]
            for score in scores
        )

        avg_chars = mean(
            score["characters"]
            for score in scores
        )

        avg_coverage = mean(
            score["coverage"]
            for score in scores
        )

        required_success = mean(
            score["all_required"]
            for score in scores
        )

        print(
            f"{name:8s} | "
            f"avg_docs={avg_docs:.1f} | "
            f"avg_chars={avg_chars:.0f} | "
            f"mean_coverage={avg_coverage:.1%} | "
            f"required_success={required_success:.1%}"
        )


if __name__ == "__main__":
    main()
