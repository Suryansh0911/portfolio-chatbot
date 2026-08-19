from app.rag.query_rewriter import rewrite_query


conversations = [

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
        "question": "Which one uses Hugging Face?"
    },

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
            },
            {
                "role": "user",
                "content": "Which one uses Hugging Face?"
            },
            {
                "role": "assistant",
                "content": (
                    "The CS-NLP Toolkit uses Hugging Face Transformers."
                )
            }
        ],
        "question": "Tell me more about that one."
    },

    {
        "history": [
            {
                "role": "user",
                "content": "What did Suryansh do at SmartED?"
            },
            {
                "role": "assistant",
                "content": (
                    "He worked as a Data Science Intern at "
                    "SmartED Innovations."
                )
            }
        ],
        "question": "What technologies did he use there?"
    },

    {
        "history": [
            {
                "role": "user",
                "content": "Tell me about Suryansh's education."
            },
            {
                "role": "assistant",
                "content": (
                    "He completed a B.Tech in Mechanical Engineering "
                    "from SVNIT."
                )
            }
        ],
        "question": "Where did he study?"
    }
]


for i, conversation in enumerate(
    conversations,
    start=1
):

    query = rewrite_query(
        conversation["question"],
        conversation["history"]
    )

    print("\n" + "=" * 70)

    print(
        f"TEST {i}"
    )

    print(
        "Original:"
    )

    print(
        conversation["question"]
    )

    print(
        "\nRewritten:"
    )

    print(
        query
    )