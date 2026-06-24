from scraper import scrape_entire_site
from embeddings import create_embedding

print("Building embeddings...")

raw_data = scrape_entire_site()

chunks = [item["chunk"] for item in raw_data]
chunks = list(set(chunks))

EMBEDDED_CHUNKS = []

for chunk in chunks:
    EMBEDDED_CHUNKS.append({
        "chunk": chunk,
        "vector": create_embedding(chunk)
    })

SITE_CONTEXT = scrape_entire_site()

print("READY:", len(EMBEDDED_CHUNKS))