import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-small-en-v1.5")


def create_embedding(text: str):
    return model.encode(text, normalize_embeddings=True).tolist()


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_top_k(question_embedding, embedded_chunks, k=3):
    scored = []

    for item in embedded_chunks:
        score = cosine_similarity(question_embedding, item["vector"])
        scored.append({
            "chunk": item["chunk"],
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    return scored[:k]