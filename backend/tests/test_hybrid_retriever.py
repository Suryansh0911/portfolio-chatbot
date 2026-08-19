from app.rag.hybrid_retriever import hybrid_retrieve


questions = [
    "What machine learning experience does Suryansh have?",
    "What NLP projects has Suryansh built?",
    "Which projects use Hugging Face?",
    "What did Suryansh do during his internship?",
    "What technologies does he know?",
    "What is Suryansh's CGPA?"
]


for question in questions:

    print("\n" + "=" * 80)
    print("QUERY:")
    print(question)

    results = hybrid_retrieve(
        question,
        top_k=4
    )

    for result in results:

        print("\n---")

        print(
            f"Category: {result['category']}"
        )

        print(
            f"Semantic: "
            f"{result['semantic_normalized']:.3f}"
        )

        print(
            f"Keyword: "
            f"{result['keyword_normalized']:.3f}"
        )

        print(
            f"Final: "
            f"{result['final_score']:.3f}"
        )

        print(result["text"])