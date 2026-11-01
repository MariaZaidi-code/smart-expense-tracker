import os
from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_documents(doc_dir):
    """Load supported text documents from a directory.

    Returns a list of dicts: {source, path, text, metadata}.
    """
    doc_dir = Path(doc_dir)
    if not doc_dir.exists():
        raise FileNotFoundError(f"document directory not found: {doc_dir}")
    if not doc_dir.is_dir():
        raise NotADirectoryError(f"not a directory: {doc_dir}")

    docs = []
    for path in sorted(doc_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1")
        text = text.strip()
        if not text:
            continue
        docs.append({
            "source": path.name,
            "path": str(path),
            "text": text,
            "metadata": {
                "source": path.name,
                "extension": path.suffix.lower(),
                "size": len(text),
            },
        })
    if not docs:
        raise ValueError(f"no supported documents found in {doc_dir}")
    return docs
