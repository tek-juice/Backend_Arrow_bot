import os
from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()

genai.configure(
    api_key=os.getenv("Gemini_API_KEY")
)
MODEL_NAME = "gemini-2.0-flash"
