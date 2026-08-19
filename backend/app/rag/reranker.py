from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

reranker = CrossEncoder(MODEL_NAME)

def rerank(
        query: str,
        documents: list[dict],
        top_k: int=3)-> list[dict]:

    if not documents:
        return []

    pairs = [
        (query, document["text"]) for document in documents
    ]

    scores = reranker.predict(pairs)

    for document, score in zip(documents, scores):
        document["rerank_score"] = float(score)

        documents.sort(
            key = lambda x : ["rerank_score"], reverse=True
        )

    return documents[:top_k]