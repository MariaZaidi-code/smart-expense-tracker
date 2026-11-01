import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from rag.retriever import retrieve, build_index
from mcp_server import tools


@pytest.fixture(scope="module")
def indexed():
    doc_dir = ROOT / "rag" / "documents"
    build_index(doc_dir)
    return True


def test_at_least_five_documents_indexed():
    from rag.vector_store import count
    assert count() >= 5


def test_retrieval_returns_passages_with_sources(indexed):
    res = retrieve("emergency fund months", top_k=3)
    assert len(res) > 0
    for r in res:
        assert r.get("text")
        assert r.get("source")
    sources = {r["source"] for r in res}
    assert len(sources) >= 1


def test_retrieval_relevance_emergency(indexed):
    res = retrieve("emergency fund", top_k=1)
    assert res
    assert "emergency" in res[0]["text"].lower() or "emergency" in res[0]["source"].lower()


def test_empty_query_returns_empty(indexed):
    assert retrieve("") == []
    assert retrieve("   ") == []


def test_search_financial_guidance_tool(indexed):
    out = tools.search_financial_guidance("budgeting rules", top_k=3)
    assert out["count"] >= 1
    assert all("source" in r and "text" in r for r in out["results"])


def test_get_budgeting_rules():
    out = tools.get_budgeting_rules()
    assert "rules" in out
    assert len(out["rules"]) >= 1


def test_mcp_tool_error_handling_empty_retrieval(indexed, tmp_path, monkeypatch):
    # force empty collection by using a fresh persist dir with no index
    import os
    empty_dir = tmp_path / "empty_chroma"
    monkeypatch.setenv("CHROMA_DIR", str(empty_dir))
    out = tools.search_financial_guidance("anything")
    # Should not crash; may be empty
    assert "results" in out
    assert isinstance(out["results"], list)


def test_health_check():
    out = tools.health_check()
    assert out["status"] == "ok"
