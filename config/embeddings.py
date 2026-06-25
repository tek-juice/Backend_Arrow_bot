from fastembed import TextEmbedding

embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


def get_embedding(text: str):
    return list(embedder.embed([text]))[0].tolist()


def get_embeddings(texts: list[str]):
    return [embedding.tolist() for embedding in embedder.embed(texts)]