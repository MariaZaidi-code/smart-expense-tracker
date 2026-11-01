import subprocess
import sys
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module")
def server():
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # wait for server
    import urllib.request
    for _ in range(50):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    yield "http://127.0.0.1:5000"
    proc.terminate()
    proc.wait(timeout=10)


def test_homepage_loads(page: Page, server):
    page.goto(server)
    expect(page).to_have_title("Expense Tracker RAG")


def test_search_returns_results(page: Page, server):
    page.goto(server)
    page.fill("#q", "emergency fund")
    page.click("#btn")
    page.wait_for_selector(".result", timeout=15000)
    results = page.locator(".result")
    assert results.count() >= 1
    text = results.first.inner_text()
    assert "emergency" in text.lower() or "fund" in text.lower()


def test_empty_query_shows_empty_or_error(page: Page, server):
    page.goto(server)
    page.click("#btn")
    # either empty message or no results; ensure no crash
    page.wait_for_timeout(1000)
    assert page.title() == "Expense Tracker RAG"
