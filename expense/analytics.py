from expense.transactions import list_transactions
from expense.budgets import list_budgets, get_budget

VALID_CATEGORIES = {
    "Food", "Transport", "Utilities", "Entertainment",
    "Shopping", "Health", "Other",
}


def total_spending(month=None, category=None, db_path=None):
    txns = list_transactions(month=month, category=category, db_path=db_path)
    return round(sum(t["amount"] for t in txns), 2)


def category_breakdown(month=None, db_path=None):
    txns = list_transactions(month=month, db_path=db_path)
    result = {c: 0.0 for c in VALID_CATEGORIES}
    for t in txns:
        result[t["category"]] = result.get(t["category"], 0.0) + t["amount"]
    return {k: round(v, 2) for k, v in result.items() if v != 0 or True}


def remaining_budget(month, category=None, db_path=None):
    budgets = list_budgets(month=month, db_path=db_path)
    bmap = {b["category"]: b["amount"] for b in budgets}
    breakdown = category_breakdown(month=month, db_path=db_path)
    if category:
        spent = breakdown.get(category, 0.0)
        bud = bmap.get(category, bmap.get("ALL"))
        if bud is None:
            return {"month": month, "category": category, "budget": None,
                    "spent": spent, "remaining": None}
        return {"month": month, "category": category, "budget": bud,
                "spent": spent, "remaining": round(bud - spent, 2)}
    # all categories
    out = {}
    for cat in VALID_CATEGORIES:
        spent = breakdown.get(cat, 0.0)
        bud = bmap.get(cat, bmap.get("ALL"))
        out[cat] = {
            "budget": bud,
            "spent": spent,
            "remaining": None if bud is None else round(bud - spent, 2),
        }
    return {"month": month, "categories": out}


def month_comparison(month_a, month_b, db_path=None):
    def agg(m):
        txns = list_transactions(month=m, db_path=db_path)
        total = sum(t["amount"] for t in txns)
        cats = {}
        for t in txns:
            cats[t["category"]] = cats.get(t["category"], 0.0) + t["amount"]
        return total, cats

    total_a, cats_a = agg(month_a)
    total_b, cats_b = agg(month_b)
    return {
        "month_a": month_a,
        "month_b": month_b,
        "total_a": round(total_a, 2),
        "total_b": round(total_b, 2),
        "difference": round(total_b - total_a, 2),
        "categories_a": {k: round(v, 2) for k, v in cats_a.items()},
        "categories_b": {k: round(v, 2) for k, v in cats_b.items()},
    }


def unusual_spending(month, threshold=2.0, db_path=None):
    # transparent rule: category spending > threshold * (average monthly category
    # spending across all months) flagged.
    all_txns = list_transactions(db_path=db_path)
    months = sorted({t["date"][:7] for t in all_txns})
    if month not in months:
        return []
    # average per category per month across other months
    cat_month_totals = {}
    for t in all_txns:
        m = t["date"][:7]
        cat_month_totals.setdefault(m, {}).setdefault(t["category"], 0.0)
        cat_month_totals[m][t["category"]] += t["amount"]

    current = cat_month_totals.get(month, {})
    flags = []
    for cat, spent in current.items():
        others = [cat_month_totals[m].get(cat, 0.0) for m in months if m != month]
        if not others:
            continue
        avg = sum(others) / len(others) if others else 0.0
        if avg > 0 and spent > threshold * avg:
            flags.append({
                "category": cat,
                "spent": round(spent, 2),
                "average_other_months": round(avg, 2),
                "ratio": round(spent / avg, 2),
                "reason": "spending exceeds threshold multiple of historical average",
            })
        elif avg == 0 and spent > 0:
            flags.append({
                "category": cat,
                "spent": round(spent, 2),
                "average_other_months": 0.0,
                "ratio": None,
                "reason": "new spending in category with no prior history",
            })
    return flags
