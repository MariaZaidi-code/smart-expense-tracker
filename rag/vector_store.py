import os
from pathlib import Path

import chromadb

DEFAULT_PERSIST_DIR = os.environ.get(
    "CHROMA_DIR",
    str(Path(__file__).resolve().parent.parent / "data" / "chroma"),
)
COLLECTION_NAME = "financial_guidance"


def get_client(persist_dir=None):
    d = persist_dir or DEFAULT_PERSIST_DIR
    Path(d).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=d)


def get_collection(persist_dir=None, name=COLLECTION_NAME):
    client = get_client(persist_dir)
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def reset_collection(persist_dir=None, name=COLLECTION_NAME):
    client = get_client(persist_dir)
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def add_chunks(chunks, embeddings, persist_dir=None):
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings length mismatch")
    col = get_collection(persist_dir)
    ids = [f"{c['source']}::{c['chunk_id']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c.get("metadata", {}) for c in chunks]
    col.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    return len(ids)


def count(persist_dir=None):
    return get_collection(persist_dir).count()


def query(embedding, top_k=5, persist_dir=None):
    col = get_collection(persist_dir)
    if col.count() == 0:
        return []
    res = col.query(query_embeddings=[embedding], n_results=min(top_k, col.count()))
    out = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    ids = res.get("ids", [[]])[0]
    for i, text in enumerate(docs):
        meta = metas[i] if i < len(metas) else {}
        out.append({
            "id": ids[i] if i < len(ids) else None,
            "text": text,
            "source": meta.get("source"),
            "metadata": meta,
            "distance": dists[i] if i < len(dists) else None,
        })
    return out
