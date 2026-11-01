def chunk_text(text, chunk_size=500, overlap=100):
    """Split text into overlapping chunks by character count (word-safe)."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >=0 and < chunk_size")
    text = (text or "").strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        # try to break at whitespace
        if end < n:
            ws = text.rfind(" ", start, end)
            if ws > start + chunk_size // 2:
                end = ws
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_documents(docs, chunk_size=500, overlap=100):
    out = []
    for doc in docs:
        for i, c in enumerate(chunk_text(doc["text"], chunk_size, overlap)):
            out.append({
                "source": doc["source"],
                "text": c,
                "chunk_id": i,
                "metadata": {**doc.get("metadata", {}), "chunk": i},
            })
    return out
