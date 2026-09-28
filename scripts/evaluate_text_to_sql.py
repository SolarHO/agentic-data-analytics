from app.evaluation.cases import EVALUATION_CASES
from app.evaluation.evaluator import compare_result
from app.graph.analysis_graph import analysis_graph


def main():
    total = len(EVALUATION_CASES)
    passed = 0

    print("=== Text-to-SQL Evaluation ===")
    print(f"Total cases: {total}\n")

    for case in EVALUATION_CASES:
        case_id = case["id"]
        question = case["question"]
        expected = case["expected"]

        print("=" * 60)
        print(f"[{case_id}]")
        print(f"Question: {question}")

        try:
            result = analysis_graph.invoke(
                {
                    "question": question,
                }
            )

            sql = result.get("sql", "")
            sql_valid = result.get("sql_valid", False)
            validation_error = result.get("validation_error")
            execution_error = result.get("execution_error")
            actual = result.get("result", [])

            print("\nGenerated SQL:")
            print(sql)

            if not sql_valid:
                print("\nResult: FAIL")
                print(f"Validation error: {validation_error}")
                continue

            if execution_error:
                print("\nResult: FAIL")
                print(f"Execution error: {execution_error}")
                continue

            success, errors = compare_result(
                actual=actual,
                expected=expected,
            )

            print("\nExpected:")
            print(expected)

            print("\nActual:")
            print(actual)

            if success:
                passed += 1
                print("\nResult: PASS")
            else:
                print("\nResult: FAIL")
                for error in errors:
                    print(f"- {error}")

        except Exception as exc:
            print("\nResult: ERROR")
            print(f"{type(exc).__name__}: {exc}")

        print()

    accuracy = (passed / total * 100) if total else 0

    print("=" * 60)
    print("=== Evaluation Summary ===")
    print(f"Passed: {passed}/{total}")
    print(f"Execution Accuracy: {accuracy:.2f}%")


if __name__ == "__main__":
    main()