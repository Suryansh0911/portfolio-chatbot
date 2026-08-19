import re
from rank_bm25 import BM25Okapi
from app.rag.reranker import rerank
from app.rag.embeddings import create_query_embedding
from app.rag.vector_store import search_vector_store, load_documents

INTENT_CATEGORY_MAP = {
    "education": {"education"},
    "experience": {"experience"},
    "project": {"project"},
    "skills": {"skills"},
    "certification": {"certification"},
    "achievement": {"achievement"},
    "personal": {"personal"},
}


def intent_category_score(
    intent: str | None,
    category: str
) -> float:

    if not intent:
        return 0.0

    return float(
        category in INTENT_CATEGORY_MAP.get(
            intent,
            set()
        )
    )

def tokenize(text: str) -> list[str]:
    """
    Simple tokenizer for BM25.
    """

    return re.findall(
        r"\b\w+\b",
        text.lower()
    )


def build_bm25(documents: list[dict]):

    tokenized_documents = [
        tokenize(document["text"])
        for document in documents
    ]

    return BM25Okapi(
        tokenized_documents
    )


def min_max_normalize(
        scores: list[float])->list[float]:

    if not scores:
        return []

    minimum = min(scores)
    maximum = max(scores)

    if maximum == minimum:
        return [1.0] * len(scores)

    return [
        (score - minimum) / (maximum - minimum) for score in scores
    ]


def category_bonus(
    query: str,
    category: str,
    intent: str | None = None) -> float:

    if intent == "project":
        return 0.20 if category == "project" else 0.0

    if intent == "experience":
        return 0.20 if category == "experience" else 0.0

    if intent == "summary":
        return 0.10 if category == "summary" else 0.0

    if intent == "evaluation":
        if category in {
            "skills",
            "experience",
            "project"
        }:
            return 0.10

    query = query.lower()

    if "internship" in query or "experience" in query:
        return 0.15 if category == "experience" else 0.0

    if "project" in query:
        return 0.10 if category == "project" else 0.0

    if (
        "education" in query
        or "degree" in query
        or "qualification" in query
        or "cgpa" in query
    ):
        return 0.15 if category == "education" else 0.0

    if (
        "skill" in query
        or "technology" in query
        or "technologies" in query
        or "tools" in query
    ):
        return 0.15 if category == "skills" else 0.0

    return 0.0


def hybrid_retrieve(
    query: str,
    top_k: int = 4,
    intent: str | None = None
) -> list[dict]:

    documents = load_documents()

    # 1. Semantic retrieval

    candidate_k = min(
    8,
    len(documents)
)

    semantic_results_raw = search_vector_store(
        query,
        top_k=candidate_k
    )

    semantic_results = {
        result["index"]: result["semantic_score"]
        for result in semantic_results_raw
    }

    # 2. BM25 retrieval

    bm25 = build_bm25(documents)

    query_tokens = tokenize(query)

    bm25_scores = bm25.get_scores(query_tokens)

    keyword_candidates = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True
    )[:candidate_k]

    # 3. Combine candidates

    candidate_indices = set(
        semantic_results.keys()
    )

    candidate_indices.update(
        keyword_candidates
    )

    # 4. Build candidate documents

    results = []

    for index_position in candidate_indices:

        semantic_score = semantic_results.get(
            index_position,
            0.0
        )

        keyword_score = float(
            bm25_scores[index_position]
        )

        results.append({
            "index": index_position,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "category": documents[index_position]["category"],
            "text": documents[index_position]["text"]
        })

    if not results:
        return []

    # 5. Normalize semantic + keyword scores

    semantic_normalized = min_max_normalize(
        [
            result["semantic_score"]
            for result in results
        ]
    )

    keyword_normalized = min_max_normalize(
        [
            result["keyword_score"]
            for result in results
        ]
    )

    for result, semantic_score, keyword_score in zip(
        results,
        semantic_normalized,
        keyword_normalized
    ):

        result["semantic_normalized"] = semantic_score
        result["keyword_normalized"] = keyword_score

    # 6. Initial hybrid score

    for result in results:

        metadata_score = category_bonus(
            query,
            result["category"],
            intent
        )

        result["metadata_score"] = metadata_score

        result["final_score"] = (
            0.70 * result["semantic_normalized"]
            +
            0.30 * result["keyword_normalized"]
            +
            metadata_score
        )

    # 7. Candidate selection

    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    candidate_results = results[:8]

    # 8. Cross-encoder reranking

    reranked_results = rerank(
        query,
        candidate_results,
        top_k=len(candidate_results)
    )

    if not reranked_results:
        return []

    # 9. Normalize reranker scores

    rerank_scores = [
        result.get(
            "rerank_score",
            -10.0
        )
        for result in reranked_results
    ]

    rerank_normalized = min_max_normalize(
        rerank_scores
    )

    # 10. Final intent-aware ranking

    for result, rerank_score in zip(
        reranked_results,
        rerank_normalized
    ):

        intent_score = intent_category_score(
            intent,
            result["category"]
        )

        result["intent_score"] = intent_score
        result["rerank_normalized"] = rerank_score

        result["final_rerank_score"] = (
            0.20 * result["semantic_normalized"]
            +
            0.20 * result["keyword_normalized"]
            +
            0.45 * rerank_score
            +
            0.15 * intent_score
        )

    # 11. Final ranking

    reranked_results.sort(
        key=lambda x: x["final_rerank_score"],
        reverse=True
    )

    return reranked_results[:top_k]