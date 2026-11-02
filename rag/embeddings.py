"""Embedding backends for the RAG pipeline.

Primary backend: Sentence Transformers (``all-MiniLM-L6-v2``).
Offline fallback: a deterministic scikit-learn HashingVectorizer.  The fallback
keeps the demo and tests reproducible when the model cannot be downloaded, and
it still produces real vector embeddings stored in the vector database.

Set ``EMBEDDING_BACKEND=hashing`` to force the fallback, or
``EMBEDDING_BACKEND=sentence-transformers`` to force the model.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

BACKEND_ENV = "EMBEDDING_BACKEND"
_MODEL_NAME = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_model = None
_model_failed = False


def _model_is_cached() -> bool:
    """Avoid a long network download when the model is not cached locally."""
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    target = "models--sentence-transformers--all-MiniLM-L6-v2"
    return (cache / target).exists()


def embedding_backend() -> str:
    forced = os.environ.get(BACKEND_ENV, "auto").lower()
    if forced in {"hashing", "sentence-transformers", "auto"}:
        return forced
    return "auto"


def _get_model():
    global _model, _model_failed
    if _model is not None or _model_failed:
        return _model
    try:
        from sentence_transformers import SentenceTransformer

        # MCP speaks JSON-RPC over stdout. Model loaders and progress bars must
        # never write to that stream, so redirect library output to stderr.
        with contextlib.redirect_stdout(sys.stderr):
            _model = SentenceTransformer(_MODEL_NAME)
    except Exception:
        _model_failed = True
        _model = None
    return _model


def _hashing_embeddings(texts: list[str], dim: int = 384) -> list[list[float]]:
    from sklearn.feature_extraction.text import HashingVectorizer

    vectorizer = HashingVectorizer(
        n_features=dim,
        alternate_sign=False,
        norm="l2",
        lowercase=True,
    )
    matrix = vectorizer.transform(texts)
    return matrix.toarray().astype("float32").tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    backend = embedding_backend()
    if backend == "sentence-transformers" or (backend == "auto" and _model_is_cached()):
        model = _get_model()
        if model is not None:
            with contextlib.redirect_stdout(sys.stderr):
                vectors = model.encode(
                    list(texts), convert_to_numpy=True, normalize_embeddings=True
                )
            return [vector.tolist() for vector in vectors]
    return _hashing_embeddings(texts)


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0] if text else []


def backend_name() -> str:
    """Human-readable backend actually used on the next call."""
    backend = embedding_backend()
    if backend == "sentence-transformers":
        return f"sentence-transformers ({_MODEL_NAME})"
    if backend == "hashing":
        return "hashing-vectorizer (offline fallback)"
    if _model_is_cached() or _model is not None:
        return f"sentence-transformers ({_MODEL_NAME})"
    return "hashing-vectorizer (offline fallback)"
