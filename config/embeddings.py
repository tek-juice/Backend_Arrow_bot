from fastembed import TextEmbedding

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embedder


def get_embedding(text: str):
    embedder = get_embedder()
    return list(embedder.embed([text]))[0].tolist()