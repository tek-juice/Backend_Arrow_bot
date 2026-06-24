from flask import Blueprint, jsonify

from chunk import chunk_text
from scraper import scrape_entire_site
from embeddings import create_embedding

debug_bp = Blueprint("debug", __name__)

@debug_bp.route("/debug-chunks")
def debug_chunks():

    raw_data = scrape_entire_site()

    chunks = []

    for item in raw_data:

        text_chunks = chunk_text(item["text"])

        for i, chunk in enumerate(text_chunks):

            chunks.append({
                "source": item["source"],
                "chunk_id": i,
                "text": chunk,
                "word_count": len(chunk.split())
            })

    return jsonify({
        "total_chunks": len(chunks),
        "avg_chunk_size": (
            sum(c["word_count"] for c in chunks)
            / len(chunks)
        ),
        "samples": chunks[:5]
    })

@debug_bp.route("/debug-embeddings")
def debug_embeddings():

    raw_data = scrape_entire_site()

    chunks = []

    for item in raw_data:

        text_chunks = chunk_text(item["text"])

        chunks.extend(text_chunks)

    embeddings = []

    for chunk in chunks:

        embeddings.append({
            "chunk": chunk,
            "vector": create_embedding(chunk)
        })

    return jsonify({
        "total_chunks": len(chunks),
        "total_embeddings": len(embeddings),
        "vector_size": len(embeddings[0]["vector"]),
        "samples": [
            {
                "chunk": e["chunk"][:300],
                "vector_preview": e["vector"][:10]
            }
            for e in embeddings[:5]
        ]
    })