from app.rag.hybrid_retriever import hybrid_retrieve
from app.rag.confidence import calculate_retrieval_confidence
from app.rag.abstention import should_abstain


QUESTIONS = [

    "What did Suryansh do at SmartED?",

    "What NLP projects has Suryansh built?",

    "What technologies does Suryansh know?",

    "Has Suryansh worked at Google?",

    "What is Suryansh's experience with quantum computing?",

    "Has Suryansh worked at Microsoft?",
]


for question in QUESTIONS:

    results = hybrid_retrieve(
        question,
        top_k=3
    )

    confidence = calculate_retrieval_confidence(
        results
    )

    abstain = should_abstain(
        results,
        confidence
    )

    print("\n" + "=" * 70)

    print(
        f"QUESTION: {question}"
    )

    print(
        f"CONFIDENCE: {confidence:.3f}"
    )

    print(
        f"ABSTAIN: {abstain}"
    )

    if results:

        print("\nTOP RESULTS:")

        for result in results:

            print(
                f"{result['category']} | "
                f"rerank={result.get('rerank_score', 0):.4f}"
            )