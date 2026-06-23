from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flasgger import Swagger, swag_from
from chunk import chunk_text
from embeddings import create_embedding, retrieve_top_k

from scraper import scrape_entire_site
from llm import stream_ollama

from warmModel import warmup_model

app = Flask(__name__)
CORS(app)

print("building embeddings...")

raw_data = scrape_entire_site()

# already chunked in scraper → no re-chunking
chunks = [item["chunk"] for item in raw_data]

# remove duplicates
chunks = list(set(chunks))

EMBEDDED_CHUNKS = []

for c in chunks:
    EMBEDDED_CHUNKS.append({
        "chunk": c,
        "vector": create_embedding(c)
    })

print("READY:", len(EMBEDDED_CHUNKS))


swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger = Swagger(app, config=swagger_config)

print("loading website data...")
SITE_CONTEXT = scrape_entire_site()
print("website loaded!")

warmup_model()


@app.route("/chat", methods=["POST"])
@swag_from({
    "tags": ["Chat"],
    "description": "Ask question about Arrow Conveyancing website",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    ],
    "responses": {
        200: {"description": "AI response"}
    }
})
def chat():
    data = request.get_json() or {}
    question = data.get("question")

    if not question:
        return jsonify({"error": "question is required"}), 400

   
    answer = "".join(stream_ollama(SITE_CONTEXT, question))

    return jsonify({"answer": answer})


@app.route("/chat-stream", methods=["POST"])
@swag_from({
    "tags": ["Chat Streaming"],
    "description": "Stream AI response token-by-token",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    ],
    "responses": {
        200: {"description": "Streaming response"}
    }
})
def chat_stream():
    data = request.get_json() or {}
    question = data.get("question")

    if not question:
        return jsonify({"error": "question is required"}), 400

    def generate():
        # 1. embed question
        q_embedding = create_embedding(question)

        # 2. retrieve top chunks
        top_chunks = retrieve_top_k(q_embedding, EMBEDDED_CHUNKS, k=3)

        # 3. build context
        context = "\n\n".join([c["chunk"][:400] for c in top_chunks])

        # 4. stream to LLM
        for chunk in stream_ollama(context, question):
            yield chunk

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain"
    )

@app.route("/debug-chunks", methods=["GET"])
@swag_from({
    "tags": ["Debug"],
    "description": "Returns scraped website chunks for testing chunking logic",
    "responses": {
        200: {
            "description": "List of chunks with metadata",
            "schema": {
                "type": "object",
                "properties": {
                    "total_chunks": {"type": "integer"},
                    "avg_chunk_size": {"type": "number"},
                    "samples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "chunk_id": {"type": "integer"},
                                "text": {"type": "string"},
                                "word_count": {"type": "integer"}
                            }
                        }
                    }
                }
            }
        }
    }
})
def debug_chunks():
    raw_data = scrape_entire_site()

    chunks = []

    if isinstance(raw_data, list):
        for item in raw_data:
            text_chunks = chunk_text(item["text"])
            for i, ch in enumerate(text_chunks):
                chunks.append({
                    "source": item["source"],
                    "chunk_id": i,
                    "text": ch,
                    "word_count": len(ch.split())
                })
    else:
        text_chunks = chunk_text(raw_data)
        for i, ch in enumerate(text_chunks):
            chunks.append({
                "source": "full_site",
                "chunk_id": i,
                "text": ch,
                "word_count": len(ch.split())
            })

    return jsonify({
        "total_chunks": len(chunks),
        "avg_chunk_size": sum(c["word_count"] for c in chunks) / len(chunks) if chunks else 0,
        "samples": chunks[:5]
    })

@app.route("/debug-embeddings", methods=["GET"])
@swag_from({
    "tags": ["Debug"],
    "description": "Test chunking + embedding generation pipeline",
    "responses": {
        200: {
            "description": "Embeddings test result",
            "schema": {
                "type": "object",
                "properties": {
                    "total_chunks": {"type": "integer"},
                    "total_embeddings": {"type": "integer"},
                    "vector_size": {"type": "integer"},
                    "samples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "chunk": {"type": "string"},
                                "vector_preview": {
                                    "type": "array",
                                    "items": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
})
def debug_embeddings():
    raw_data = scrape_entire_site()

    chunks = []

    for item in raw_data:
        text_chunks = chunk_text(item["text"])
        for ch in text_chunks:
            chunks.append(ch)

    embeddings = []

    for chunk in chunks:
        vec = create_embedding(chunk)
        embeddings.append({
            "chunk": chunk,
            "vector": vec
        })

    # return small preview only (important!)
    samples = []
    for e in embeddings[:5]:
        samples.append({
            "chunk": e["chunk"][:300],
            "vector_preview": e["vector"][:10]  # first 10 dims only
        })

    return jsonify({
        "total_chunks": len(chunks),
        "total_embeddings": len(embeddings),
        "vector_size": len(embeddings[0]["vector"]) if embeddings else 0,
        "samples": samples
    })

@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "swagger": "/apidocs/"
    })


if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000,
        threaded=True,
        use_reloader=False  # IMPORTANT: prevents model reload on restart loops
    )