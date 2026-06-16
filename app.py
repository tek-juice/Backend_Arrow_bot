from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flasgger import Swagger, swag_from

from scraper import scrape_entire_site
from llm import stream_ollama  # IMPORTANT: must yield tokens

app = Flask(__name__)
CORS(app)

# ✅ FIX: proper swagger config so /apidocs works
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


# =========================
# NON-STREAM CHAT (optional)
# =========================
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
                    "question": {"type": "string", "example": "What services do they offer?"}
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

    answer = stream_ollama(SITE_CONTEXT, question, stream=False)
    return jsonify({"answer": answer})


# =========================
# STREAMING CHAT (REALTIME)
# =========================
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
        200: {
            "description": "Streaming response (text/plain)"
        }
    }
})
def chat_stream():
    data = request.get_json() or {}
    question = data.get("question")

    if not question:
        return jsonify({"error": "question is required"}), 400

    def generate():
        # stream word/token chunks
        for chunk in stream_ollama(SITE_CONTEXT, question, stream=True):
            yield chunk

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain"
    )


# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "swagger": "/apidocs/"
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)