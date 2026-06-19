from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flasgger import Swagger, swag_from

from scraper import scrape_entire_site
from llm import stream_ollama

from warmModel import warmup_model

app = Flask(__name__)
CORS(app)


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
        for chunk in stream_ollama(SITE_CONTEXT, question):
            yield chunk

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain"
    )

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