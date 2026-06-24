from flask import Blueprint, request, jsonify, Response, stream_with_context
from flasgger import swag_from
from embeddings import create_embedding, retrieve_top_k
from llm import stream_ollama
from shared.vector_store import EMBEDDED_CHUNKS, SITE_CONTEXT

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
@swag_from({
    "tags": ["Chat"],
    "description": "Ask a question about Arrow Conveyancing",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string"
                    }
                },
                "required": ["question"]
            }
        }
    ],
    "responses": {
        200: {
            "description": "AI response"
        },
        400: {
            "description": "Validation error"
        }
    }
})
def chat():

    data = request.get_json() or {}
    question = data.get("question")

    if not question:
        return jsonify({
            "error": "question is required"
        }), 400

    answer = "".join(
        stream_ollama(
            SITE_CONTEXT,
            question
        )
    )

    return jsonify({
        "answer": answer
    })

@chat_bp.route("/chat-stream", methods=["POST"])
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
                    "question": {
                        "type": "string"
                    }
                },
                "required": ["question"]
            }
        }
    ],
    "responses": {
        200: {
            "description": "Streaming response"
        },
        400: {
            "description": "Validation error"
        }
    }
})
def chat_stream():

    data = request.get_json() or {}
    question = data.get("question")

    if not question:
        return jsonify({
            "error": "question is required"
        }), 400

    def generate():

        q_embedding = create_embedding(question)

        top_chunks = retrieve_top_k(
            q_embedding,
            EMBEDDED_CHUNKS,
            k=3
        )

        context = "\n\n".join(
            [chunk["chunk"][:400] for chunk in top_chunks]
        )

        for token in stream_ollama(
            context,
            question
        ):
            yield token

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain"
    )