# Expense Tracker AI - Qaim Module (RAG + MCP Server)

This repository implements the RAG and MCP Server portion (Part 2) of the
"Expense Tracker AI Agent" project, plus supporting expense/budget functions.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Build the knowledge base

```bash
python build_index.py
```

This loads the markdown files in `rag/documents/`, chunks them, embeds them with
Sentence Transformers (`all-MiniLM-L6-v2`), and stores them in ChromaDB under
`data/chroma`.

## Run the MCP server

```bash
python mcp_server/server.py
```

The server uses stdio transport (MCP) and exposes tools such as
`search_financial_guidance`, `get_budgeting_rules`, `add_expense`,
`get_spending_summary`, `get_budget_status`, etc.

## Run the MCP client demo

```bash
python mcp_client/client_demo.py
```

## Run tests

```bash
python -m pytest -q
```

## Architecture

- `rag/document_loader.py` loads `.txt`/`.md` documents with source metadata.
- `rag/chunker.py` splits documents into overlapping chunks.
- `rag/embeddings.py` generates embeddings via Sentence Transformers.
- `rag/vector_store.py` persists embeddings in ChromaDB and supports semantic query.
- `rag/retriever.py` exposes `build_index` and `retrieve` (returns passages + sources).
- `mcp_server/tools.py` implements business logic (RAG + expense/budget functions).
- `mcp_server/server.py` wraps the logic in an MCP server (FastMCP, stdio).
- `mcp_client/client_demo.py` is a Python MCP client that invokes tools and prints results.
- `expense/*` and `database/*` provide the expense/budget functions exposed via MCP
  without duplicating calculation logic.

## Error handling

Empty retrieval results, missing documents, malformed requests, and unavailable
services are handled gracefully and returned as structured error responses rather
than crashes.

## Evidence

- `tests/test_rag_mcp.py`: retrieval relevance, source attribution, MCP tool execution.
- `tests/test_expenses.py`: database operations, calculations, invalid inputs.
- `mcp_client/client_demo.py`: end-to-end MCP invocation output.
