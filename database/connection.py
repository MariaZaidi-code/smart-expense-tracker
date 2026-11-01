import os
import sqlite3
from pathlib import Path

def default_db_path():
    return os.environ.get(
        "EXPENSE_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "expenses.db"),
    )


def get_connection(db_path=None):
    path = db_path or default_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None, schema_path=None):
    conn = get_connection(db_path)
    if schema_path is None:
        schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    return conn
