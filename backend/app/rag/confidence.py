import math


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def calculate_retrieval_confidence(
    results: list[dict]
) -> float:

    if not results:
        return 0.0

    scores = sorted(
        [
            result.get(
                "final_rerank_score",
                0.0
            )
            for result in results
        ],
        reverse=True
    )

    top_score = scores[0]

    if len(scores) == 1:
        return round(top_score, 3)

    second_score = scores[1]

    margin = max(
        0.0,
        top_score - second_score
    )

    margin_score = min(
        margin / 0.5,
        1.0
    )

    confidence = (
        0.7 * top_score
        +
        0.3 * margin_score
    )

    return round(
        max(0.0, min(1.0, confidence)),
        3
    )