"""SQLite connection, schema, and path helpers shared by every module.

Both the Streamlit UI (Rameen) and the MCP/RAG layer (Qaim) use this module, so
the whole project reads and writes one database.  Set ``EXPENSE_DB_PATH`` to
point at a different file (tests do this with ``tmp_path``).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "expenses.db"
SCHEMA_PATH = ROOT / "database" / "schema.sql"


def get_db_path() -> Path:
    """Return the active database path (environment override wins)."""
    return Path(os.environ.get("EXPENSE_DB_PATH", DEFAULT_DB_PATH))


def default_db_path() -> str:
    """Qaim-compatible alias returning the path as a string."""
    return str(get_db_path())


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: str | Path | None = None, schema_path: str | Path | None = None) -> None:
    """Create every table/index from ``schema.sql`` if it does not exist."""
    schema = Path(schema_path) if schema_path else SCHEMA_PATH
    with get_connection(db_path) as connection:
        connection.executescript(schema.read_text(encoding="utf-8"))


def init_db(db_path: str | Path | None = None, schema_path: str | Path | None = None) -> sqlite3.Connection:
    """Qaim-compatible helper: ensure the schema exists and return a connection.

    Callers own the returned connection and should close it.
    """
    path = db_path or get_db_path()
    initialize_database(path, schema_path)
    return get_connection(path)
