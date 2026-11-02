"""Merchant -> category memory.

Leading apps (Copilot Money, Monarch) win on auto-categorisation that *learns
from the user*.  Every time a transaction is saved, this module records the
merchant/category pair.  Future entries for the same merchant are suggested
automatically, and the confidence grows with repeated confirmations.
"""

from __future__ import annotations

import re
from pathlib import Path

from database.connection import get_connection

# Tokens that appear on statements but do not identify the merchant.
_NOISE = {
    "card",
    "pos",
    "payment",
    "purchase",
    "online",
    "debit",
    "credit",
    "txn",
    "transaction",
    "ref",
    "invoice",
    "bill",
    "the",
    "and",
    "pk",
    "pvt",
    "ltd",
}

# Fallback keyword map used until the user has taught the app anything.
_KEYWORDS = {
    "Food & dining": [
        "restaurant", "cafe", "kitchen", "biryani", "pizza", "burger", "chai",
        "coffee", "brunch", "lunch", "dinner", "bakery", "food", "dining",
    ],
    "Groceries": ["grocer", "mart", "basket", "supermarket", "imtiaz", "alfatah", "fresh"],
    "Transport": ["careem", "uber", "metro", "fuel", "petrol", "shell", "total", "parking", "bus", "taxi"],
    "Bills & utilities": ["ptcl", "internet", "electric", "wapda", "sui", "gas", "water", "phone", "bill", "utility"],
    "Entertainment": ["netflix", "spotify", "youtube", "cinema", "cinepax", "game", "movie", "concert"],
    "Shopping": ["amazon", "daraz", "store", "mall", "clothes", "stationery", "shop"],
    "Health": ["pharmacy", "clinic", "hospital", "doctor", "gym", "fitness", "medicine", "dental"],
    "Education": ["course", "udemy", "coursera", "tuition", "book", "school", "university"],
}


def normalize_merchant(description: str) -> str:
    """Turn a statement description into a stable merchant key."""
    text = (description or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token and token not in _NOISE]
    # Drop pure reference numbers.
    tokens = [token for token in tokens if not token.isdigit()]
    return " ".join(tokens)[:80]


def remember_merchant_category(
    description: str,
    category: str,
    db_path: str | Path | None = None,
) -> dict | None:
    merchant = normalize_merchant(description)
    if not merchant or not category:
        return None
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT id, times_used FROM merchant_rules WHERE merchant = ?",
            (merchant,),
        ).fetchone()
        if row:
            times_used = int(row["times_used"]) + 1
            confidence = min(0.99, 0.5 + 0.08 * times_used)
            connection.execute(
                """
                UPDATE merchant_rules
                SET category = ?, times_used = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (category, times_used, confidence, row["id"]),
            )
        else:
            connection.execute(
                """
                INSERT INTO merchant_rules(merchant, category, times_used, confidence)
                VALUES (?, ?, 1, 0.58)
                """,
                (merchant, category),
            )
        saved = connection.execute(
            "SELECT * FROM merchant_rules WHERE merchant = ?", (merchant,)
        ).fetchone()
    return dict(saved) if saved else None


def _keyword_category(merchant: str) -> str | None:
    tokens = set(re.findall(r"[a-z0-9]+", merchant))
    for category, keywords in _KEYWORDS.items():
        if tokens & set(keywords):
            return category
    return None


def _categories_available(db_path=None) -> set[str]:
    with get_connection(db_path) as connection:
        return {row["name"] for row in connection.execute("SELECT name FROM categories")}


def suggest_category(
    description: str,
    db_path: str | Path | None = None,
) -> dict:
    """Return the best category guess for a merchant description.

    Resolution order: an exact learned rule -> a fuzzy learned rule (token
    overlap) -> built-in keyword heuristic.  The response always explains the
    source so the UI can say *why* it suggested something.
    """
    merchant = normalize_merchant(description)
    available = _categories_available(db_path)
    if not merchant:
        return {"category": None, "confidence": 0.0, "source": "empty description"}

    with get_connection(db_path) as connection:
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM merchant_rules ORDER BY times_used DESC, confidence DESC"
            )
        ]

    for row in rows:
        if row["merchant"] == merchant:
            return {
                "category": row["category"],
                "confidence": round(float(row["confidence"]), 2),
                "source": f"learned from {row['times_used']} saved transaction(s)",
                "merchant": merchant,
            }

    merchant_tokens = set(merchant.split())
    best = None
    best_overlap = 0.0
    for row in rows:
        tokens = set(row["merchant"].split())
        if not tokens:
            continue
        overlap = len(merchant_tokens & tokens) / len(merchant_tokens | tokens)
        if overlap > best_overlap:
            best_overlap, best = overlap, row
    if best and best_overlap >= 0.5:
        return {
            "category": best["category"],
            "confidence": round(min(0.9, 0.4 + best_overlap * 0.4), 2),
            "source": f"matched earlier merchant '{best['merchant']}'",
            "merchant": merchant,
        }

    keyword = _keyword_category(merchant)
    if keyword and keyword in available:
        return {
            "category": keyword,
            "confidence": 0.45,
            "source": "keyword heuristic (no learned rule yet)",
            "merchant": merchant,
        }
    return {
        "category": None,
        "confidence": 0.0,
        "source": "no matching rule or keyword",
        "merchant": merchant,
    }


def list_rules(db_path: str | Path | None = None, limit: int = 100) -> list[dict]:
    with get_connection(db_path) as connection:
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT * FROM merchant_rules
                ORDER BY times_used DESC, confidence DESC, merchant
                LIMIT ?
                """,
                (int(limit),),
            )
        ]


def clear_rules(db_path: str | Path | None = None) -> int:
    with get_connection(db_path) as connection:
        cursor = connection.execute("DELETE FROM merchant_rules")
        return cursor.rowcount
