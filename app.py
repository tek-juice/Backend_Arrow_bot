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

        prompt = f"""
You are a chatbot assistant for arrow conveyancing company.
Answer using the COMPANY SITE CONTENT plus including all your knowledge base.
{SITE_CONTENT}


USER QUESTION: 
{question}"""

        response = model.generate_content(prompt)
        raw_text = response.text

        clean_text = re.sub(r":\s*\n\s*\n+", ":\n", raw_text)

        clean_text = re.sub(r"\n\s*\n+", "\n", clean_text)

        clean_text = re.sub(r":\n([^\-\*\n])", r":\n- \1", clean_text)

        clean_text = re.sub(r"\n\*\s+", "\n- ", clean_text)

        clean_text = re.sub(r"\n[ \t]+", "\n", clean_text)

        clean_text = clean_text.replace(":", "")
        clean_text = re.sub(r"These include\b", "These", clean_text, flags=re.IGNORECASE)

        clean_text = clean_text.strip()
        return jsonify({
            "answer": clean_text
        })
    
    except Exception as e:
        return jsonify({
            "error": "Failed to generate response try again later",
            "details": str(e)
        }), 500
    
if __name__ == "__main__":
    app.run(debug=True)