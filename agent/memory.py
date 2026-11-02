"""Short-term and long-term memory for the expense agent.

Short-term memory is the per-session transcript stored in ``agent_messages``.
Long-term memory is a durable key/value store in ``agent_memory`` that is
retrieved by user id in a brand-new session (the Assignment 2 requirement).

Both use the same SQLite database as the expense data, so a single
``EXPENSE_DB_PATH`` environment variable switches the whole demo.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import date
from pathlib import Path

from database.connection import initialize_database, get_connection

DEFAULT_USER_ID = "demo_user"


def _slug(value: str, fallback: str = "note") -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return (slug or fallback)[:80]


def new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:12]}"


class MemoryStore:
    def __init__(
        self,
        user_id: str = DEFAULT_USER_ID,
        db_path: str | Path | None = None,
    ):
        self.user_id = user_id
        self.db_path = db_path
        initialize_database(db_path)

    # ------------------------------------------------------------------
    # Short-term memory
    # ------------------------------------------------------------------
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        tools_used: list[str] | None = None,
        sources: list[dict] | None = None,
    ) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO agent_messages(session_id, user_id, role, content, tools_used, sources)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.user_id,
                    role,
                    content,
                    json.dumps(tools_used or []),
                    json.dumps(sources or [], default=str),
                ),
            )
            return int(cursor.lastrowid)

    def history(self, session_id: str, limit: int = 20) -> list[dict]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT role, content, tools_used, sources, created_at
                FROM agent_messages
                WHERE session_id = ? AND user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, self.user_id, limit),
            ).fetchall()
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "tools_used": json.loads(row["tools_used"] or "[]"),
                "sources": json.loads(row["sources"] or "[]"),
                "created_at": row["created_at"],
            }
            for row in reversed(rows)
        ]

    def history_for_llm(self, session_id: str, limit: int = 16) -> list[dict]:
        return [
            {"role": item["role"], "content": item["content"]}
            for item in self.history(session_id, limit=limit)
        ]

    def clear_session(self, session_id: str) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM agent_messages WHERE session_id = ? AND user_id = ?",
                (session_id, self.user_id),
            )
            return cursor.rowcount

    def sessions(self) -> list[dict]:
        with get_connection(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT session_id, COUNT(*) AS messages, MIN(created_at) AS started,
                       MAX(created_at) AS last_message
                FROM agent_messages
                WHERE user_id = ?
                GROUP BY session_id
                ORDER BY last_message DESC
                """,
                (self.user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # Long-term memory
    # ------------------------------------------------------------------
    def remember(
        self,
        key: str,
        value: str,
        category: str = "fact",
        importance: int = 3,
    ) -> dict:
        memory_key = _slug(key)
        memory_value = (value or "").strip()[:1000]
        if not memory_value:
            raise ValueError("Memory value is required.")
        importance = max(1, min(int(importance), 5))
        with get_connection(self.db_path) as connection:
            connection.execute(
                """
                INSERT INTO agent_memory(user_id, memory_key, memory_value, category, importance)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, memory_key) DO UPDATE SET
                    memory_value = excluded.memory_value,
                    category = excluded.category,
                    importance = excluded.importance,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (self.user_id, memory_key, memory_value, category, importance),
            )
            row = connection.execute(
                "SELECT * FROM agent_memory WHERE user_id = ? AND memory_key = ?",
                (self.user_id, memory_key),
            ).fetchone()
        return dict(row) if row else {}

    def recall(self, query: str = "", limit: int = 20) -> list[dict]:
        limit = max(1, min(int(limit), 100))
        with get_connection(self.db_path) as connection:
            if query and query.strip():
                pattern = f"%{query.strip().lower()}%"
                rows = connection.execute(
                    """
                    SELECT * FROM agent_memory
                    WHERE user_id = ?
                      AND (LOWER(memory_key) LIKE ? OR LOWER(memory_value) LIKE ? OR LOWER(category) LIKE ?)
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (self.user_id, pattern, pattern, pattern, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM agent_memory
                    WHERE user_id = ?
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (self.user_id, limit),
                ).fetchall()
        return [dict(row) for row in rows]

    def all_facts(self, limit: int = 100) -> list[dict]:
        return self.recall(limit=limit)

    def forget(self, memory_key: str) -> bool:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM agent_memory WHERE user_id = ? AND memory_key = ?",
                (self.user_id, _slug(memory_key)),
            )
            return cursor.rowcount > 0

    def clear_long_term(self) -> int:
        with get_connection(self.db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM agent_memory WHERE user_id = ?", (self.user_id,)
            )
            return cursor.rowcount

    def format_for_prompt(self, limit: int = 20) -> str:
        facts = self.all_facts(limit=limit)
        if not facts:
            return ""
        return "\n".join(
            f"- {fact['memory_key']}: {fact['memory_value']} ({fact['category']})"
            for fact in facts
        )

    # ------------------------------------------------------------------
    # Rule-based fact extraction (works without an LLM)
    # ------------------------------------------------------------------
    def extract_facts(self, message: str) -> list[dict]:
        text = (message or "").strip()
        lowered = text.lower()
        # "What do you remember?" is a recall question, not a fact to store.
        if re.search(r"\b(what|do|did|can|could|would)\b[^.?]*\bremember\b", lowered):
            return []
        facts: list[dict] = []

        def add(key: str, value: str, category: str = "fact", importance: int = 3):
            if value and value.strip():
                facts.append(
                    {
                        "key": _slug(key),
                        "value": value.strip()[:300],
                        "category": category,
                        "importance": importance,
                    }
                )

        name = re.search(
            r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,40}?)(?=\s+and\b|\s*,|\.|$)",
            text,
            re.I,
        )
        if name:
            add("name", name.group(1).strip(" ."), "profile", 5)

        location = re.search(
            r"\bi (?:live|am based) in\s+([A-Za-z][A-Za-z .'-]{1,40}?)(?=\s+and\b|\s*,|\.|$)",
            text,
            re.I,
        )
        if location:
            add("location", location.group(1).strip(" ."), "profile", 4)

        budget = re.search(
            r"\bmy\s+(?:(?:monthly|annual)\s+)?"
            r"(?:(food|transport|utilities|entertainment|shopping|health|groceries|bills)\s+)?"
            r"budget\s+(?:is|=|of)\s*(?:rs\.?|pkr|₨)?\s*([\d,]+(?:\.\d+)?)",
            text,
            re.I,
        )
        if budget:
            scope = (budget.group(1) or "monthly").lower()
            value = budget.group(2).replace(",", "")
            add(f"budget_{scope}", value, "budget", 5)

        income = re.search(
            r"\bmy\s+(?:monthly\s+)?(?:income|salary)\s+(?:is|=|of)\s*(?:rs\.?|pkr|₨)?\s*([\d,]+(?:\.\d+)?)",
            text,
            re.I,
        )
        if income:
            add("monthly_income", income.group(1).replace(",", ""), "profile", 5)

        savings = re.search(
            r"\b(?:i(?:'m| am)?\s+(?:saving|trying to save)|my savings goal is)\s+(?:for\s+)?(?:rs\.?|pkr|₨)?\s*([\d,]+(?:\.\d+)?)?\s*(?:for\s+)?([A-Za-z][A-Za-z ]{0,60})?",
            text,
            re.I,
        )
        if savings and (savings.group(1) or savings.group(2)):
            amount = (savings.group(1) or "").replace(",", "")
            purpose = (savings.group(2) or "").strip(" .")
            value = " ".join(part for part in (amount, purpose) if part).strip()
            if value:
                add("savings_goal", value, "goal", 5)

        preference = re.search(
            r"\bi (?:prefer|like|love|hate|avoid|always use|never use)\s+(.{3,120})",
            text,
            re.I,
        )
        if preference:
            fragment = preference.group(1).strip(" .")
            add(f"preference_{_slug(fragment)[:40]}", fragment, "preference", 4)

        remember = re.search(r"\b(?:remember|note|don'?t forget)\s+(?:that\s+)?(.{4,200})", text, re.I)
        if remember:
            fragment = remember.group(1).strip(" .")
            if fragment.lower() not in {"that", "this", "it", "that.", "this."}:
                add(f"note_{_slug(fragment)[:50]}", fragment, "note", 4)

        favorite = re.search(
            r"\bmy (?:favourite|favorite) (?:category|spending category) is\s+([A-Za-z &]{2,40})",
            text,
            re.I,
        )
        if favorite:
            add("favorite_category", favorite.group(1).strip(" ."), "preference", 4)

        salary_day = re.search(
            r"\b(?:salary|payday|income)\s+(?:arrives|comes|is)\s+(?:on\s+)?(?:the\s+)?([0-9]{1,2}(?:st|nd|rd|th)?(?:\s+of\s+(?:the\s+)?month)?)",
            text,
            re.I,
        )
        if salary_day:
            add("salary_day", salary_day.group(1).strip(), "profile", 4)

        # Explicit "remember that ..." should always be stored even if the
        # generic preference patterns did not match.
        if lowered.startswith("remember") and not facts:
            fragment = re.sub(r"^remember\s+(?:that\s+)?", "", lowered).strip(" .")
            if len(fragment) >= 4 and fragment not in {"this", "it"}:
                add(f"note_{_slug(text)[:50]}", text, "note", 4)

        # De-duplicate by key, keeping the last value.
        deduped: dict[str, dict] = {}
        for fact in facts:
            deduped[fact["key"]] = fact
        return list(deduped.values())

    def save_extracted_facts(self, message: str) -> list[dict]:
        saved = []
        for fact in self.extract_facts(message):
            saved.append(
                self.remember(
                    fact["key"],
                    fact["value"],
                    category=fact["category"],
                    importance=fact["importance"],
                )
            )
        return saved


class ShortTermMemory(MemoryStore):
    """Explicit alias for readability in tests and docs."""


class LongTermMemory(MemoryStore):
    """Explicit alias used by the MCP memory tools."""


def current_month() -> str:
    return date.today().strftime("%Y-%m")
