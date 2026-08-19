from app.rag.hybrid_retriever import hybrid_retrieve
from app.rag.reranker import rerank


questions = [
    "What machine learning experience does Suryansh have?",
    "What NLP projects has Suryansh built?",
    "What did Suryansh do during his internship?",
    "What technologies does Suryansh know?",
]


for question in questions:

    print("\n" + "=" * 80)
    print("QUERY:")
    print(question)


    results = hybrid_retrieve(
        question,
        top_k=3
    )

    print("\nRERANKED RESULTS:")

    for result in results:

        print("\n---")

        print(
            f"Category: {result['category']}"
        )

        print(
            f"Hybrid score: "
            f"{result['final_score']:.4f}"
        )

        print(
            f"Rerank score: "
            f"{result['rerank_score']:.4f}"
        )

        print(result["text"])