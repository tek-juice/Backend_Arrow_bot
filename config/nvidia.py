import os
from openai import OpenAI
from dotenv import load_dotenv

from config.vector_search import search_documents
from config.memory_service import build_chat_session

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

MODEL = "meta/llama-3.1-8b-instruct"


def stream_answer(session_id: int, question: str):
    # 1. RAG retrieval
    results = search_documents(question, top_k=3)

    documents = [row[0] for row in results]

    context = "\n\n".join(
        doc.chunk[:150] for doc in documents
    )

    # 2. Build chat memory
    messages = build_chat_session(session_id, question)

    # 3. Inject system + RAG context
    messages.insert(0, {
        "role": "system",
        "content": f"""
You are Arrow Conveyancing assistant.

Use ONLY the context below.

If not found, use general knowledge.

Context:
{context}
"""
    })

    # 4. Call model
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.2,
        stream=True,
        timeout=120,
    )

    # 5. Stream response safely
    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        if not delta:
            continue

        token = getattr(delta, "content", None)
        if token:
            yield token