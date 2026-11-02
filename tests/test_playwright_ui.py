import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_UI_TESTS") != "1",
    reason="Set RUN_UI_TESTS=1 to run the Flask/Playwright integration test.",
)


@pytest.fixture(scope="module")
def server():
    playwright = pytest.importorskip("playwright.sync_api")
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/health", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    yield "http://127.0.0.1:5000"
    proc.terminate()
    proc.wait(timeout=10)


def test_homepage_loads(server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(server)
        assert page.title() == "Expense Tracker RAG"
        browser.close()


def test_search_returns_results(server):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(server)
        page.fill("#q", "emergency fund")
        page.click("#btn")
        page.wait_for_selector(".result", timeout=15000)
        assert page.locator(".result").count() >= 1
        browser.close()
