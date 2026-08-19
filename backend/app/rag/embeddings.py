from sentence_transformers import SentenceTransformer

modelname = "all-MiniLM-L6-v2"
model = SentenceTransformer(modelname)

def create_embeddings(texts: list[str]):
    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )


def create_query_embedding(query: str):
    return model.encode(
        [query], 
        convert_to_numpy=True,
        normalize_embeddings=True
    )