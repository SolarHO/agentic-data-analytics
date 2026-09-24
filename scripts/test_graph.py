from app.graph.analysis_graph import analysis_graph


def main():
    initial_state = {
        "question": "평균 주문 금액은 얼마야?"
    }

    result = analysis_graph.invoke(initial_state)

    print("=== Question ===")
    print(result["question"])

    print("\n=== Generated SQL ===")
    print(result["sql"])

    print("\n=== SQL Validation ===")
    print("sql_valid:", result["sql_valid"])
    print("validation_error:", result["validation_error"])

    print("\n=== Execution Result ===")
    print(result["result"])

    print("\n=== Execution Error ===")
    print(result["execution_error"])


if __name__ == "__main__":
    main()