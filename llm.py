import ollama

def stream_ollama(context: str, question: str, model="qwen2.5:3b"):
    prompt = f"""
You are an AI assistant for Arrow Conveyancing company.

Use ONLY the context below.
If not found, say: "Please contact support."

Context:
{context}

Question:
{question}
"""

    stream = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    for chunk in stream:
        content = chunk.get("message", {}).get("content", "")
        if content:
            yield content