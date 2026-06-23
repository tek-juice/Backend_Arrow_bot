def chunk_text(
    text: str,
    chunk_size: int = 350,
    overlap: int = 50
):
    """
    Chunk by paragraphs while preserving context.
    """

    paragraphs = [
        p.strip()
        for p in text.split("\n")
        if p.strip()
    ]

    chunks = []
    current_chunk = []

    current_length = 0

    for paragraph in paragraphs:

        words = paragraph.split()

        if current_length + len(words) > chunk_size:

            chunks.append(" ".join(current_chunk))

            overlap_words = (
                current_chunk[-overlap:]
                if overlap > 0
                else []
            )

            current_chunk = overlap_words.copy()
            current_length = len(current_chunk)

        current_chunk.extend(words)
        current_length += len(words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks