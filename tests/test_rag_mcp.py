import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

# Keep the test index out of the demo index.
os.environ.setdefault("CHROMA_DIR", tempfile.mkdtemp(prefix="expense-chroma-"))

import pytest

from rag.retriever import build_index, retrieve
from rag.vector_store import count


@pytest.fixture(scope="module", autouse=True)
def indexed():
    build_index(ROOT / "rag" / "documents")
    return True


def test_at_least_five_documents_indexed():
    assert count() >= 5


def test_retrieval_returns_passages_with_sources():
    results = retrieve("emergency fund months", top_k=3)
    assert len(results) > 0
    for result in results:
        assert result.get("text")
        assert result.get("source")
    assert len({result["source"] for result in results}) >= 1


def test_retrieval_relevance_emergency():
    results = retrieve("emergency fund", top_k=3)
    assert results
    combined = " ".join(result["text"].lower() for result in results)
    assert "emergency" in combined or "fund" in combined


def test_empty_query_returns_empty():
    assert retrieve("") == []
    assert retrieve("   ") == []


def test_search_financial_guidance_tool():
    from mcp_server import tools

    out = tools.search_financial_guidance("budgeting rules", top_k=3)
    assert out["count"] >= 1
    assert all("source" in result and "text" in result for result in out["results"])


def test_get_budgeting_rules():
    from mcp_server import tools

    out = tools.get_budgeting_rules()
    assert "rules" in out
    assert len(out["rules"]) >= 1


def test_empty_index_returns_no_crash(tmp_path, monkeypatch):
    import rag.vector_store as vector_store

    monkeypatch.setattr(vector_store, "DEFAULT_PERSIST_DIR", str(tmp_path / "empty"))
    out = retrieve("anything", persist_dir=str(tmp_path / "empty"))
    assert out == []


def test_health_check():
    from mcp_server import tools

    out = tools.health_check()
    assert out["status"] == "ok"
