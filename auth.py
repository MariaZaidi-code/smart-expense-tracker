"""Simple user authentication for the expense tracker.

This is intentionally lightweight (password hashing with a salt) and is meant
for a teaching/demo deployment.  Production use should replace it with a real
identity provider.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path

from database.connection import get_connection


def _hash(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, digest


def hash_password(password: str) -> str:
    salt, digest = _hash(password)
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == digest


def create_user(
    username: str,
    password: str,
    display_name: str = "",
    db_path: str | Path | None = None,
) -> int:
    username = (username or "").strip().lower()
    if not username:
        raise ValueError("Username is required.")
    if len(password) < 4:
        raise ValueError("Password must be at least 4 characters.")
    with get_connection(db_path) as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            raise ValueError("That username is already taken.")
        cursor = connection.execute(
            "INSERT INTO users(username, password_hash, display_name) VALUES (?, ?, ?)",
            (username, hash_password(password), display_name.strip() or username),
        )
        return int(cursor.lastrowid)


def authenticate(username: str, password: str, db_path=None) -> dict | None:
    username = (username or "").strip().lower()
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return dict(row)


def get_user(user_id: int, db_path=None) -> dict | None:
    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def ensure_default_user(db_path=None) -> int:
    with get_connection(db_path) as connection:
        row = connection.execute("SELECT id FROM users LIMIT 1").fetchone()
        if row:
            return int(row["id"])
    return create_user("demo", "demo", "Demo User", db_path=db_path)
