import ollama

def warmup_model():
    print("Warming up model...")

    ollama.chat(
        model="qwen2.5:3b",
        messages=[{"role": "user", "content": "hello"}]
    )

    print("Model loaded and ready")