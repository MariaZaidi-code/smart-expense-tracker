import pytest

from agent.llm import GrokLLM, load_api_key, parse_key_text


def test_parse_key_text_supports_comments_and_assignments():
    assert parse_key_text("# comment\n\nxai-abc123\n") == "xai-abc123"
    assert parse_key_text("GROK_API_KEY=xai-xyz789") == "xai-xyz789"
    assert parse_key_text("XAI_API_KEY=xai-quoted\n") == "xai-quoted"
    assert parse_key_text("# only comments\n") == ""


def test_load_api_key_from_explicit_file(tmp_path):
    key_file = tmp_path / "grok_api_key.txt"
    key_file.write_text("# my key\nxai-test-key-123\n", encoding="utf-8")
    assert load_api_key(key_file) == "xai-test-key-123"


def test_grok_llm_status_without_key(monkeypatch):
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    # Point candidate files at a temporary empty directory.
    import agent.llm as llm_module

    monkeypatch.setattr(llm_module, "KEY_FILE_CANDIDATES", ())
    llm = GrokLLM(api_key="")
    assert llm.available is False
    assert llm.status()["provider"] == "Local fallback"


@pytest.mark.skipif(not load_api_key(), reason="No Grok/Groq API key configured")
def test_live_grok_optional():
    llm = GrokLLM()
    result = llm.chat(
        [{"role": "user", "content": "Reply with the single word: OK"}],
        max_tokens=10,
    )
    assert "ok" in result.content.lower()
