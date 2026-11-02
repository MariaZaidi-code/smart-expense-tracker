"""Build and query the financial-guidance knowledge base."""

from __future__ import annotations

from pathlib import Path

from rag.chunker import chunk_documents
from rag.document_loader import load_documents
from rag.embeddings import embed_query, embed_texts
from rag.vector_store import (
    add_chunks,
    count as vs_count,
    query as vs_query,
    reset_collection,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOC_DIR = ROOT / "rag" / "documents"


def build_index(
    doc_dir: str | Path = DEFAULT_DOC_DIR,
    persist_dir: str | Path | None = None,
    reset: bool = True,
    chunk_size: int = 500,
    overlap: int = 100,
) -> dict:
    documents = load_documents(doc_dir)
    chunks = chunk_documents(documents, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        raise ValueError("no chunks produced")
    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    if reset:
        reset_collection(persist_dir)
    added = add_chunks(chunks, embeddings, persist_dir)
    return {"documents": len(documents), "chunks": added}


def retrieve(query_text: str, top_k: int = 5, persist_dir: str | Path | None = None) -> list[dict]:
    if not query_text or not str(query_text).strip():
        return []
    try:
        query_embedding = embed_query(str(query_text))
    except Exception:
        return []
    results = vs_query(query_embedding, top_k=top_k, persist_dir=persist_dir)
    for result in results:
        if not result.get("source"):
            result["source"] = (result.get("metadata") or {}).get("source", "unknown")
    return results


def has_index(persist_dir: str | Path | None = None) -> bool:
    try:
        return vs_count(persist_dir) > 0
    except Exception:
        return False


def ensure_index(
    doc_dir: str | Path = DEFAULT_DOC_DIR,
    persist_dir: str | Path | None = None,
) -> dict:
    """Build the index on first use so a fresh clone works immediately."""
    if has_index(persist_dir):
        return {"documents": None, "chunks": vs_count(persist_dir), "reused": True}
    info = build_index(doc_dir=doc_dir, persist_dir=persist_dir, reset=True)
    return {**info, "reused": False}
