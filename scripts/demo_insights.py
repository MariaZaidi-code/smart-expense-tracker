"""CLI demo for the researched standout features.

Run from the project root:

    python scripts\\demo_insights.py

It seeds synthetic data, then prints the Safe-to-Spend snapshot, month-end
forecast, detected subscriptions, financial health breakdown, monthly recap,
goal progress, an affordability verdict, and a debt payoff comparison.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.seed import seed_database
from expense.goals import goal_summary
from expense.insights import (
    can_i_afford,
    debt_payoff,
    financial_health,
    month_forecast,
    monthly_recap,
    safe_to_spend,
    subscription_summary,
)
from expense.rules import suggest_category


def money(value: float) -> str:
    return f"Rs. {float(value):,.0f}"


def main() -> None:
    seed_database()
    month = date.today().strftime("%Y-%m")

    print("=" * 78)
    print(f"SAFE TO SPEND — {month}")
    snapshot = safe_to_spend(month)
    print("-" * 78)
    print(f"Safe to spend   : {money(snapshot['safe_to_spend'])} ({snapshot['label']})")
    print(f"Budget          : {money(snapshot['budget'])}")
    print(f"Spent           : {money(snapshot['spent'])}")
    print(f"Reserved bills  : {money(snapshot['upcoming_commitments'])}")
    print(f"Daily allowance : {money(snapshot['per_day'])} for {snapshot['days_left']} days")

    print("\n" + "=" * 78)
    print("MONTH-END FORECAST")
    print("-" * 78)
    forecast = month_forecast(month)
    print(f"Projected total : {money(forecast['projected_total'])}")
    print(f"Budget          : {money(forecast['budget'])}")
    print(f"Run rate        : {money(forecast['daily_run_rate'])}/day")
    print(f"Status          : {forecast['label']}")

    print("\n" + "=" * 78)
    print("SUBSCRIPTION HUNTER")
    print("-" * 78)
    subscriptions = subscription_summary()
    print(
        f"{subscriptions['count']} active · {money(subscriptions['monthly_total'])}/month "
        f"· {money(subscriptions['annual_total'])}/year"
    )
    for item in subscriptions["items"]:
        hike = " · PRICE HIKE" if item["price_hike"] else ""
        print(
            f"  - {item['description']:<24} {money(item['monthly_cost']):>12}/mo "
            f"{item['cadence']:<9} next {item['next_due']} ({item['confidence']:.0f}%){hike}"
        )

    print("\n" + "=" * 78)
    print("FINANCIAL HEALTH")
    print("-" * 78)
    health = financial_health(month)
    print(f"Score: {health['score']}/100 (grade {health['grade']})")
    for component in health["components"]:
        print(f"  - {component['label']:<20} {component['score']:>5.1f}/100  {component['detail']}")
    print(f"Next step: {health['next_step']}")

    print("\n" + "=" * 78)
    print("MONTHLY RECAP")
    print("-" * 78)
    recap = monthly_recap(month)
    print(recap["headline"])
    for bullet in recap["bullets"]:
        print(f"  - {bullet}")

    print("\n" + "=" * 78)
    print("GOALS")
    print("-" * 78)
    goals = goal_summary()
    print(f"{goals['count']} goals · {goals['progress_percent']}% funded overall")
    for goal in goals["goals"]:
        print(
            f"  - {goal['name']:<18} {money(goal['saved_amount'])} / "
            f"{money(goal['target_amount'])} · {goal['status']}"
        )

    print("\n" + "=" * 78)
    print("CAN I AFFORD IT?")
    print("-" * 78)
    for amount in (1500, 25000, 60000):
        verdict = can_i_afford(amount, month)
        print(f"  {money(amount):>12}: {verdict['message']}")

    print("\n" + "=" * 78)
    print("MERCHANT AUTO-CATEGORISATION")
    print("-" * 78)
    for merchant in ("Netflix.com", "Careem ride", "Chai Corner"):
        suggestion = suggest_category(merchant)
        print(
            f"  {merchant:<18} -> {suggestion['category']} "
            f"({float(suggestion['confidence']) * 100:.0f}%, {suggestion['source']})"
        )

    print("\n" + "=" * 78)
    print("DEBT PAYOFF PLANNER")
    print("-" * 78)
    plan = debt_payoff(
        [
            {"name": "Credit card", "balance": 120000, "apr": 24, "min_payment": 6000},
            {"name": "Personal loan", "balance": 300000, "apr": 12, "min_payment": 12000},
        ],
        extra_payment=5000,
    )
    print(plan["summary"])
    print(f"  Avalanche: {plan['avalanche']['months']} months · {money(plan['avalanche']['total_interest'])} interest")
    print(f"  Snowball : {plan['snowball']['months']} months · {money(plan['snowball']['total_interest'])} interest")

    print("\nDone. Open Smart Insights and Goals in the Streamlit app for the same data.")


if __name__ == "__main__":
    main()
