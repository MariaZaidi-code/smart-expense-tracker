import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request, render_template_string
from rag.retriever import retrieve

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head><title>Expense Tracker RAG</title></head>
<body>
  <h1>Financial Guidance Search</h1>
  <input id="q" type="text" placeholder="Ask about budgeting..." />
  <button id="btn">Search</button>
  <div id="results"></div>
  <script>
    document.getElementById('btn').onclick = async () => {
      const q = document.getElementById('q').value;
      const res = await fetch('/search', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({query: q})});
      const data = await res.json();
      const div = document.getElementById('results');
      div.innerHTML = '';
      (data.results || []).forEach(r => {
        const p = document.createElement('p');
        p.className = 'result';
        p.textContent = r.source + ': ' + r.text;
        div.appendChild(p);
      });
      if ((data.results||[]).length === 0) {
        const p = document.createElement('p');
        p.className = 'empty';
        p.textContent = 'No results';
        div.appendChild(p);
      }
    };
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "")
    if not query or not str(query).strip():
        return jsonify({"error": "query required", "results": []}), 400
    try:
        results = retrieve(query, top_k=3)
    except Exception as e:
        return jsonify({"error": str(e), "results": []}), 500
    out = [{"source": r.get("source"), "text": r.get("text")} for r in results]
    return jsonify({"results": out})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port)
