
from app.rag.retriever import search_context


QUESTIONS = [
    "배송 지연율을 계산하려면 어떤 테이블이 필요해?",
    "평균 주문 금액은 어떻게 계산해야 해?",
    "상품 카테고리별 매출을 분석하고 싶어.",
    "월별 주문 수와 매출 추이를 알고 싶어.",
    "긍정 리뷰와 부정 리뷰를 어떻게 구분해?",
]


def main():
    for question in QUESTIONS:
        print("=" * 70)
        print(f"Question: {question}")

        results = search_context(
            question=question,
            top_k=5,
        )

        for index, result in enumerate(results, start=1):
            print(
                f"{index}. "
                f"[{result['doc_type']}] "
                f"{result['name']} | "
                f"Similarity: {result['similarity']:.4f}"
            )

        print()


if __name__ == "__main__":
    main()
