import os
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _groq_key():
    return os.environ.get("GROQ_API_KEY")


def _openrouter_key():
    return os.environ.get("OPENROUTER_API_KEY")


@pytest.mark.skipif(not _groq_key(), reason="GROQ_API_KEY not set")
def test_groq_llm_optional():
    key = _groq_key()
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": "Reply with the word OK."}],
            "max_tokens": 5,
        },
        timeout=30,
    )
    if resp.status_code in (401, 403):
        pytest.skip("Groq key invalid/revoked")
    assert resp.status_code == 200, resp.text


@pytest.mark.skipif(not _openrouter_key(), reason="OPENROUTER_API_KEY not set")
def test_openrouter_llm_optional():
    key = _openrouter_key()
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [{"role": "user", "content": "Reply with the word OK."}],
            "max_tokens": 5,
        },
        timeout=30,
    )
    if resp.status_code in (401, 403):
        pytest.skip("OpenRouter key invalid/revoked")
    assert resp.status_code == 200, resp.text
