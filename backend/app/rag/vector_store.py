from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import QDRANT_URL, QDRANT_API_KEY
from app.rag.documents import create_documents
from app.rag.embeddings import create_embeddings, create_query_embedding


COLLECTION_NAME = "portfolio"
VECTOR_SIZE = 384


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


def build_vector_store():
    """
    Create/recreate the Qdrant collection and upload
    the portfolio documents and their embeddings.
    """

    documents = create_documents()

    texts = [
        document["text"]
        for document in documents
    ]

    embeddings = create_embeddings(
        texts
    )

    # Recreate the collection so indexing is deterministic.
    if client.collection_exists(
        COLLECTION_NAME
    ):
        client.delete_collection(
            COLLECTION_NAME
        )

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )

    points = []

    for index, (document, embedding) in enumerate(
        zip(documents, embeddings)
    ):

        points.append(
            PointStruct(
                id=index,
                vector=embedding.tolist(),
                payload={
                    "index": index,
                    "category": document["category"],
                    "text": document["text"]
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(
        f"Qdrant collection '{COLLECTION_NAME}' "
        f"created with {len(documents)} documents."
    )


def search_vector_store(
    query: str,
    top_k: int = 8
) -> list[dict]:

    query_embedding = create_query_embedding(
        query
    )[0]

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k,
        with_payload=True
    ).points

    return [
        {
            "index": point.payload["index"],
            "semantic_score": float(point.score),
            "category": point.payload["category"],
            "text": point.payload["text"]
        }
        for point in results
    ]

def load_documents() -> list[dict]:
    return create_documents()