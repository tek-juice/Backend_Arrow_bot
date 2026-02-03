from flask import Flask, request, jsonify
from config import genai, MODEL_NAME
from content_fetcher import fetch_multiple_pages
from flask_cors import CORS

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

        prompt = f"""
You are a chatbot assistant for arrow conveyancing company.
Your name is Arrow chat.
Answer using this information plus including all your knowledeg base.

COMPANY SITE CONTENT:
{SITE_CONTENT}

USER QUESTION: 
{question}"""

        response = model.generate_content(
            prompt
        )
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