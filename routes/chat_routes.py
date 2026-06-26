from flask import Blueprint, request, Response, stream_with_context, jsonify
from config.nvidia import stream_answer
from flasgger import swag_from

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Ask the AI assistant a question",
    "description": "Uses pgvector retrieval + NVIDIA LLM to answer questions based on your knowledge base. Response is streamed token-by-token.",
    
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "example": "What is the conveyancing process?"
                    }
                },
                "required": ["question"]
            }
        }
    ],

    "responses": {
        200: {
            "description": "Streaming AI response (text/plain token stream)"
        },
        400: {
            "description": "Validation error - missing question"
        },
        500: {
            "description": "Server error"
        }
    }
})
def chat():
    data = request.get_json() or {}
    question = data.get("question")

    if not question:
        return jsonify({
            "error": "A question is required"
        }), 400
    
    def generate():
        yield "ROUTE HIT\n"
        for token in stream_answer(question):
            yield token + "\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype="text/plain",
        headers={
            "X-Accel-Buffering": "no"   # prevents buffering (important on some setups)
        }
    )