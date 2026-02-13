from flask import Flask, request, jsonify
from config import model
from content_fetcher import fetch_multiple_pages
from flask_cors import CORS
from flasgger import Swagger

app = Flask(__name__)
CORS(app)


swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "info": {
        "title": "Arrow Conveyancing Chat API",
        "description": "API for Arrow Conveyancing chatbot assistant",
        "version": "1.0.0"
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

SITE_URLS = [
    "https://www.arrowconveyancing.co.uk/",
    "https://www.arrowconveyancing.co.uk/services",
    "https://www.arrowconveyancing.co.uk/intermediaries",
    "https://www.arrowconveyancing.co.uk/articles",
    "https://www.arrowconveyancing.co.uk/minor-pages/careers",
    "https://www.arrowconveyancing.co.uk/minor-pages/careers#open-positions",
    "https://www.arrowconveyancing.co.uk/articles",
    "https://www.arrowconveyancing.co.uk/our-team",
    "https://www.arrowconveyancing.co.uk/contact",
    
]

print("Loading website content....")
SITE_CONTENT = fetch_multiple_pages(SITE_URLS)
print("Website Content loaded")

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat endpoint for Arrow Conveyancing assistant
    ---
    tags:
      - Chat
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - question
          properties:
            question:
              type: string
              description: User's question
              example: "What services do you offer?"
    responses:
      200:
        description: Successful response
        schema:
          type: object
          properties:
            answer:
              type: string
              description: AI-generated response
      400:
        description: Bad request - missing question
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
            details:
              type: string
    """
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400
    
    question = data["question"]

    try:
        prompt = f"""
You are a chatbot assistant for arrow conveyancing company.
Your name is Arrow chat.
Answer using this information plus including all your knowledeg base.

COMPANY SITE CONTENT:
{SITE_CONTENT}

USER QUESTION: 
{question}"""

        response = model.generate_content(prompt)
        return jsonify({
            "answer": response.text
        })
    
    except Exception as e:
        return jsonify({
            "error": "Failed to generate response try again later",
            "details": str(e)
        }), 500
    
if __name__ == "__main__":
    app.run(debug=True)