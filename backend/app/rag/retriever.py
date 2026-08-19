from app.rag.embeddings import create_query_embedding
from app.rag.vector_store import load_vector_store


def calculate_keyword_bonus(
    query: str,
    document: dict
) -> float:

    query_lower = query.lower()
    text_lower = document["text"].lower()

    bonus = 0.0

    keywords = {
    "experience": [
        "experience",
        "internship",
        "intern",
        "worked",
        "work",
        "professional"
    ],

    "project": [
        "project",
        "built",
        "developed",
        "created"
    ],

    "machine learning": [
        "machine learning",
        "scikit-learn",
        "lightgbm",
        "k-means",
        "dbscan",
        "forecasting",
        "clustering"
    ],

    "nlp": [
        "nlp",
        "natural language",
        "text",
        "sentiment",
        "translation",
        "tokenization",
        "hugging face"
    ],

    "education": [
        "education",
        "degree",
        "university",
        "college",
        "cgpa",
        "coursework"
    ],

    "skills": [
        "skills",
        "technologies",
        "technical",
        "tools",
        "frameworks"
    ]
}

    for category, category_keywords in keywords.items():

        if category in query_lower:

            for keyword in category_keywords:

                if keyword in text_lower:
                    bonus += 0.03

    return bonus


def retrieve(
    query: str,
    top_k: int = 3
) -> list[dict]:

    index, documents = load_vector_store()

    query_embedding = create_query_embedding(query)

    # Retrieve more candidates initially
    candidate_k = min(8, len(documents))

    scores, indices = index.search(
        query_embedding.astype("float32"),
        candidate_k
    )

    results = []

    for score, index_position in zip(
        scores[0],
        indices[0]
    ):

        if index_position == -1:
            continue

        document = documents[index_position]

        keyword_bonus = calculate_keyword_bonus(
            query,
            document
        )

        final_score = float(score) + keyword_bonus

        results.append({
            "score": final_score,
            "semantic_score": float(score),
            "keyword_bonus": keyword_bonus,
            "category": document["category"],
            "text": document["text"]
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]