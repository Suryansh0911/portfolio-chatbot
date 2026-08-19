def should_abstain(
    results: list[dict],
    confidence: float,
    threshold: float = 0.45
) -> bool:

    if not results:
        return True

    if confidence < threshold:
        return True

    return False