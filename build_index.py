import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rag.retriever import build_index

doc_dir = ROOT / "rag" / "documents"
info = build_index(doc_dir)
print("Indexed:", info)
