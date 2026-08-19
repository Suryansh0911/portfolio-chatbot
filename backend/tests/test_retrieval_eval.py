from app.rag.hybrid_retriever import hybrid_retrieve
from tests.evaluation_dataset import EVALUATION_DATASET

def evaluate_retrieval():
    total = len(EVALUATION_DATASET)
    passed = 0

    print("RETRIEVAL EVALUATION")

    for item in EVALUATION_DATASET:

        question = item["question"]
        expected_categories = item["expected_categories"]
        expected_keywords = item["expected_keywords"]

        results = hybrid_retrieve(question, top_k=3)

        retrieved_text = " ".join(result["text"] for result in results)

        retrieved_categories = [
            result["category"] for result in results
        ]

        category_match = any(
            category in retrieved_categories
            for category in expected_categories
        )

        keyword_matches = sum(
            keyword.lower() in retrieved_text.lower()
            for keyword in expected_keywords
        )

        keyword_coverage = (keyword_matches / len(expected_keywords))

        keyword_match = keyword_coverage >= 0.25

        success = category_match and keyword_match

        if success:
            passed += 1

        print("\nQuestion:")
        print(question)

        print("Expected categories:")
        print(expected_categories)

        print("Retrieved categories:")
        print(retrieved_categories)

        print(
            f"Keyword matches: "
            f"{keyword_matches}/{len(expected_keywords)}"
        )

        print(
        f"Keyword coverage: "
        f"{keyword_coverage:.2%}"
        )

        print(
            "RESULT:",
            "PASS ✅" if success else "FAIL ❌"
        )

        accuracy = passed / total

        print("\n" + "=" * 80)
        print(f"Retrieval accuracy: {accuracy:.2%}")
        print(f"Passed: {passed}/{total}")
        print("=" * 80)


if __name__ == "__main__":
    evaluate_retrieval()