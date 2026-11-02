"""Vector store abstraction.

Primary implementation: ChromaDB (persistent, cosine distance).
Offline fallback: a small JSON-backed cosine store with the same minimal API,
used only when ChromaDB is not installed.  The fallback keeps tests and the
demo runnable on a machine without the native Chroma dependency.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

DEFAULT_PERSIST_DIR = os.environ.get(
    "CHROMA_DIR",
    str(Path(__file__).resolve().parent.parent / "data" / "chroma"),
)
COLLECTION_NAME = "financial_guidance"

try:  # pragma: no cover - import availability differs by machine
    import chromadb

    _CHROMA_AVAILABLE = True
except Exception:  # pragma: no cover
    chromadb = None
    _CHROMA_AVAILABLE = False


def store_backend() -> str:
    return "chromadb" if _CHROMA_AVAILABLE else "json-fallback"


class _JsonCollection:
    """Minimal persistent cosine-similarity collection."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = {"ids": [], "documents": [], "embeddings": [], "metadatas": []}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data), encoding="utf-8")

    def count(self) -> int:
        return len(self._data["ids"])

    def upsert(self, ids, documents, embeddings, metadatas) -> None:
        index = {item_id: i for i, item_id in enumerate(self._data["ids"])}
        for item_id, document, embedding, metadata in zip(ids, documents, embeddings, metadatas):
            if item_id in index:
                position = index[item_id]
                self._data["documents"][position] = document
                self._data["embeddings"][position] = embedding
                self._data["metadatas"][position] = metadata
            else:
                index[item_id] = len(self._data["ids"])
                self._data["ids"].append(item_id)
                self._data["documents"].append(document)
                self._data["embeddings"].append(embedding)
                self._data["metadatas"].append(metadata)
        self._save()

    def query(self, query_embeddings, n_results=5) -> dict[str, list[list[Any]]]:
        embedding = query_embeddings[0]
        scored = []
        for index, candidate in enumerate(self._data["embeddings"]):
            dot = sum(a * b for a, b in zip(embedding, candidate))
            norm_a = math.sqrt(sum(a * a for a in embedding)) or 1.0
            norm_b = math.sqrt(sum(b * b for b in candidate)) or 1.0
            distance = 1 - (dot / (norm_a * norm_b))
            scored.append((distance, index))
        scored.sort(key=lambda pair: pair[0])
        top = scored[:n_results]
        return {
            "ids": [[self._data["ids"][i] for _, i in top]],
            "documents": [[self._data["documents"][i] for _, i in top]],
            "metadatas": [[self._data["metadatas"][i] for _, i in top]],
            "distances": [[distance for distance, _ in top]],
        }


def get_client(persist_dir: str | Path | None = None):
    if not _CHROMA_AVAILABLE:
        return None
    directory = Path(persist_dir or DEFAULT_PERSIST_DIR)
    directory.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(directory))


def get_collection(persist_dir: str | Path | None = None, name: str = COLLECTION_NAME):
    directory = Path(persist_dir or DEFAULT_PERSIST_DIR)
    if not _CHROMA_AVAILABLE:
        return _JsonCollection(directory / f"{name}.json")
    client = get_client(directory)
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def reset_collection(persist_dir: str | Path | None = None, name: str = COLLECTION_NAME):
    directory = Path(persist_dir or DEFAULT_PERSIST_DIR)
    if not _CHROMA_AVAILABLE:
        path = directory / f"{name}.json"
        if path.exists():
            path.unlink()
        return _JsonCollection(path)
    client = get_client(directory)
    try:
        client.delete_collection(name)
    except Exception:
        pass
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def add_chunks(chunks, embeddings, persist_dir: str | Path | None = None) -> int:
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings length mismatch")
    collection = get_collection(persist_dir)
    ids = [f"{chunk['source']}::{chunk['chunk_id']}" for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk.get("metadata", {}) for chunk in chunks]
    collection.upsert(
        ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
    )
    return len(ids)


def count(persist_dir: str | Path | None = None) -> int:
    return get_collection(persist_dir).count()


def query(embedding, top_k: int = 5, persist_dir: str | Path | None = None) -> list[dict]:
    collection = get_collection(persist_dir)
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=[embedding], n_results=min(int(top_k), collection.count())
    )
    out = []
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    ids = result.get("ids", [[]])[0]
    for index, text in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        out.append(
            {
                "id": ids[index] if index < len(ids) else None,
                "text": text,
                "source": (metadata or {}).get("source"),
                "metadata": metadata,
                "distance": distances[index] if index < len(distances) else None,
            }
        )
    return out
