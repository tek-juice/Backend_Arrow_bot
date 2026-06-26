from sqlalchemy import select
from config.extensions import db
from models.user import DocumentChunk
from config.embeddings import get_embedding


def search_documents(question: str, top_k: int = 5):

    query_embedding = get_embedding(question)

    stmt = (
        select(
            DocumentChunk,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        )
        .order_by("distance")
        .limit(top_k)
    )

    results = db.session.execute(stmt).all()

    return results