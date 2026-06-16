import ollama


def stream_ollama(context: str, question: str, model="qwen2.5:3b", stream=True):
    prompt = f"""
You are a helpful assistant for Arrow Conveyancing website.

Use ONLY the context below.
If not found, say: "I don't know based on the website data."

Context:
{context}

Question:
{question}
"""

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=stream
    )

    if stream:
        for chunk in response:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]
    else:
        return response["message"]["content"]