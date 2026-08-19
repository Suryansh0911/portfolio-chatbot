from app.rag.query_rewriter import rewrite_query


TEST_CASES = [

    {
        "history": [
            {
                "role": "user",
                "content": "What NLP projects has Suryansh built?"
            },
            {
                "role": "assistant",
                "content": (
                    "Suryansh has worked on the CS-NLP Toolkit, "
                    "Local AI Companion, and Rural India Translator."
                )
            }
        ],
        "question": "Which one uses Hugging Face?",
        "expected_keywords": [
            "NLP",
            "Suryansh",
            "Hugging Face"
        ]
    },

    {
        "history": [
            {
                "role": "user",
                "content": "What internships has Suryansh completed?"
            },
            {
                "role": "assistant",
                "content": (
                    "Suryansh completed internships at SmartED "
                    "Innovations and Teachnook."
                )
            }
        ],
        "question": "Which one involved sentiment analysis?",
        "expected_keywords": [
            "Suryansh",
            "internship",
            "sentiment analysis"
        ]
    }
]


for case in TEST_CASES:

    rewritten = rewrite_query(
        case["question"],
        case["history"]
    )

    print("\n" + "=" * 80)

    print("Original:")
    print(case["question"])

    print("\nRewritten:")
    print(rewritten)

    matches = sum(
        keyword.lower() in rewritten.lower()
        for keyword in case["expected_keywords"]
    )

    coverage = matches / len(
        case["expected_keywords"]
    )

    print(
        f"\nKeyword coverage: {coverage:.2%}"
    )

    if coverage >= 0.66:
        print("PASS ✅")
    else:
        print("FAIL ❌")