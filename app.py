from flask import Flask, request, jsonify
from config import genai, MODEL_NAME
from content_fetcher import fetch_multiple_pages
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

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
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"error": "Question is required"}), 400
    
    question = data["question"]

    try:
        model = genai.GenerativeModel(MODEL_NAME)

        content = SITE_CONTENT[:10000]

        prompt = f"""
    You are a chatbot assistant for arrow conveyancing company.
    Answer using the COMPANY SITE CONTENT plus your knowledge.

    {content}

    USER QUESTION:
    {question}
    """

        response = model.generate_content(prompt)

        print("MODEL RESPONSE:", response)

        raw_text = getattr(response, "text", None)

        if not raw_text:
            return jsonify({
                "error": "Model returned empty response",
                "details": str(response)
            }), 500

        clean_text = raw_text.strip()

        return jsonify({"answer": clean_text})

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "error": "Failed to generate response",
            "details": str(e)
        }), 500
    
if __name__ == "__main__":
    app.run(debug=True)