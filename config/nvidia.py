import os
from openai import OpenAI
from dotenv import load_dotenv

from config.vector_search import search_documents

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

MODEL = "meta/llama-3.3-70b-instruct"


def stream_answer(question: str):
    results = search_documents(question, top_k=3)

    documents = [row[0] for row in results]

    context = "\n\n".join(
        doc.chunk[:150] for doc in documents
    )

    prompt = f"""
You are Arrow Conveyancing assistant.

Use ONLY the context below.

If not found, Use your general knowledge.

Context:
{context}

Question:
{question}
"""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        stream=True,
        timeout=120,
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token
            