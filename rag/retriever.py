from rag.document_loader import load_documents
from rag.chunker import chunk_documents
from rag.embeddings import embed_texts, embed_query
from rag.vector_store import add_chunks, query as vs_query, count as vs_count, reset_collection

DEFAULT_DOC_DIR = None


def build_index(doc_dir, persist_dir=None, reset=True, chunk_size=500, overlap=100):
    docs = load_documents(doc_dir)
    chunks = chunk_documents(docs, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        raise ValueError("no chunks produced")
    embeddings = embed_texts([c["text"] for c in chunks])
    if reset:
        reset_collection(persist_dir)
    added = add_chunks(chunks, embeddings, persist_dir)
    return {"documents": len(docs), "chunks": added}


def retrieve(query_text, top_k=5, persist_dir=None):
    if not query_text or not str(query_text).strip():
        return []
    try:
        qemb = embed_query(query_text)
    except Exception:
        return []
    results = vs_query(qemb, top_k=top_k, persist_dir=persist_dir)
    # normalize: ensure source present
    for r in results:
        if not r.get("source"):
            r["source"] = (r.get("metadata") or {}).get("source", "unknown")
    return results


def has_index(persist_dir=None):
    try:
        return vs_count(persist_dir) > 0
    except Exception:
        return False
