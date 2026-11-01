import json
import os
import statistics
import urllib.request
from datetime import datetime, timedelta
from typing import Any

from app.config import settings

DEFAULT_CATEGORIES = ["Food", "Transport", "Housing", "Utilities", "Entertainment", "Health", "Shopping", "Education", "Other"]

KEYWORDS = {
    "Food": ["food", "lunch", "dinner", "breakfast", "restaurant", "grocery", "groceries", "coffee", "pizza", "meal", "snack"],
    "Transport": ["uber", "taxi", "bus", "train", "metro", "gas", "fuel", "parking", "flight", "transport"],
    "Housing": ["rent", "mortgage", "apartment", "house", "housing"],
    "Utilities": ["electric", "water", "internet", "phone", "utility", "gas bill", "electricity"],
    "Entertainment": ["movie", "cinema", "game", "concert", "netflix", "spotify", "entertainment"],
    "Health": ["doctor", "hospital", "pharmacy", "medicine", "health", "gym", "dental"],
    "Shopping": ["shop", "shopping", "clothes", "amazon", "mall", "store"],
    "Education": ["school", "tuition", "course", "book", "education", "college", "university"],
}


def _llm_config():
    api_key = settings.llm_api_key or os.getenv("LLM_API_KEY", "")
    base_url = settings.llm_base_url or os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    model = settings.llm_model or os.getenv("LLM_MODEL", "gpt-4o-mini")
    return api_key, base_url, model


def _llm_chat(messages):
    api_key, base_url, model = _llm_config()
    if not api_key:
        return None
    url = base_url.rstrip("/") + "/chat/completions"
    body = {"model": model, "messages": messages, "temperature": 0}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def categorize(description, amount):
    return categorize_detail(description, amount)["category"]


def categorize_detail(description, amount):
    text = (description or "").lower()
    for cat, kws in KEYWORDS.items():
        if any(kw in text for kw in kws):
            return {"category": cat, "confidence": 0.85, "source": "rules"}
    content = _llm_chat([
        {"role": "system", "content": "Classify the expense into one of: " + ", ".join(DEFAULT_CATEGORIES) + ". Reply with only the category name."},
        {"role": "user", "content": f"Description: {description}; Amount: {amount}"},
    ])
    if content:
        for cat in DEFAULT_CATEGORIES:
            if cat.lower() == content.lower().strip().strip("."):
                return {"category": cat, "confidence": 0.75, "source": "llm"}
    return {"category": "Other", "confidence": 0.5, "source": "fallback"}


def _to_list(expenses_summary):
    if isinstance(expenses_summary, list):
        return expenses_summary
    if isinstance(expenses_summary, dict):
        items = expenses_summary.get("expenses")
        if isinstance(items, list):
            return items
    return []


def _category_of(item):
    if isinstance(item, dict):
        return item.get("category") or item.get("category_name") or item.get("category_id")
    return getattr(item, "category", None) or getattr(item, "category_name", None) or getattr(item, "category_id", None)


def _amount_of(item):
    if isinstance(item, dict):
        return float(item.get("amount", 0) or 0)
    return float(getattr(item, "amount", 0) or 0)


def _date_of(item):
    if isinstance(item, dict):
        v = item.get("date")
    else:
        v = getattr(item, "date", None)
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def insights(expenses_summary):
    result = []
    items = _to_list(expenses_summary)
    if isinstance(expenses_summary, dict) and "by_category" in expenses_summary:
        by_cat = dict(expenses_summary["by_category"])
    else:
        by_cat = {}
        for item in items:
            cat = _category_of(item)
            key = cat if isinstance(cat, str) else str(cat) if cat is not None else "Other"
            by_cat[key] = by_cat.get(key, 0.0) + _amount_of(item)
    if by_cat:
        top = max(by_cat, key=lambda k: by_cat[k])
        result.append(f"Top spending category: {top} ({by_cat[top]:.2f})")
    # month-over-month
    if isinstance(expenses_summary, dict) and "monthly_totals" in expenses_summary:
        monthly = dict(expenses_summary["monthly_totals"])
    else:
        monthly = {}
        for item in items:
            d = _date_of(item)
            if d:
                key = d.strftime("%Y-%m")
                monthly[key] = monthly.get(key, 0.0) + _amount_of(item)
    if len(monthly) >= 2:
        keys = sorted(monthly)
        prev, curr = monthly[keys[-2]], monthly[keys[-1]]
        if prev:
            pct = (curr - prev) / prev * 100
            direction = "increased" if pct >= 0 else "decreased"
            result.append(f"Spending {direction} {abs(pct):.1f}% month-over-month")
        else:
            result.append(f"Spending changed to {curr:.2f} this month")
    # budget warnings
    budgets = {}
    if isinstance(expenses_summary, dict):
        budgets = expenses_summary.get("budgets") or {}
    for cat, spent in by_cat.items():
        if cat in budgets and spent > budgets[cat]:
            result.append(f"Budget exceeded for {cat}: {spent:.2f}/{budgets[cat]:.2f}")
    if not result:
        result.append("No spending data available")
    return result


def detect_anomalies(expenses):
    amounts = [_amount_of(e) for e in expenses]
    if len(amounts) < 2:
        mean = amounts[0] if amounts else 0
        std = 0
    else:
        mean = statistics.mean(amounts)
        std = statistics.pstdev(amounts)
    default_set = set(DEFAULT_CATEGORIES)
    out = []
    for e in expenses:
        amt = _amount_of(e)
        z = (amt - mean) / std if std else 0.0
        cat = _category_of(e)
        cat_name = cat if isinstance(cat, str) else None
        unusual = cat_name is not None and cat_name not in default_set
        if z > 2 or unusual:
            out.append(e)
    return out


def nl_query(question, context):
    q = (question or "").lower()
    ctx = context if isinstance(context, dict) else {"context": context}
    content = _llm_chat([
        {"role": "system", "content": "You are a helpful expense tracking assistant. Answer concisely using the provided context."},
        {"role": "user", "content": f"Context: {json.dumps(ctx, default=str)}\nQuestion: {question}"},
    ])
    if content:
        return content
    # rule-based template
    if "total" in q or "spent" in q:
        total = None
        if isinstance(ctx, dict):
            total = ctx.get("total") or ctx.get("total_expenses") or ctx.get("expense")
        if total is not None:
            return f"Total spending: {total}"
    if "top" in q and "category" in q:
        by_cat = ctx.get("by_category") if isinstance(ctx, dict) else None
        if by_cat:
            top = max(by_cat, key=lambda k: by_cat[k])
            return f"Top category: {top}"
    if "budget" in q:
        return "Review your budget warnings in insights."
    return "I couldn't determine an answer from available data."