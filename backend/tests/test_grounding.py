from app.rag.grounding import check_grounding


context = """
Suryansh Gupta worked as a Data Science Intern
at SmartED Innovations from Jan 2026 to Apr 2026.

He architected automated data ingestion and preprocessing
pipelines for 58M+ retail records.

He applied LightGBM for sales forecasting and
K-Means/DBSCAN for customer segmentation.
"""


tests = [

    {
        "question": "What did Suryansh do at SmartED?",
        "answer": (
            "Suryansh worked as a Data Science Intern at "
            "SmartED Innovations, where he built data "
            "pipelines and applied LightGBM and clustering."
        )
    },

    {
        "question": "Has Suryansh worked at Google?",
        "answer": (
            "Suryansh worked at Google as a Machine Learning "
            "Engineer before joining SmartED."
        )
    },

    {
        "question": "What did Suryansh do at SmartED?",
        "answer": (
            "Suryansh worked at SmartED and built data pipelines. "
            "He also led a team of 20 engineers."
        )
    }
]


for test in tests:

    result = check_grounding(
        test["question"],
        test["answer"],
        context
    )

    print("\n" + "=" * 70)

    print(
        "QUESTION:",
        test["question"]
    )

    print(
        "ANSWER:",
        test["answer"]
    )

    print(
        "VERDICT:",
        result["verdict"]
    )

    print(
        "REASON:",
        result["reason"]
    )