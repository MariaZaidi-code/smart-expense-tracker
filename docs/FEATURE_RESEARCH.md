# Competitive Research → Implemented Features

The brief for this round was: *find tools like Smart Expense Tracker, identify the
features that stand out, and integrate them into this project.*

I reviewed the product positioning and 2026 round-ups for the leading personal
budgeting apps, extracted the one or two features each is known for, and rebuilt
the useful ones on top of the existing SQLite data layer. Everything below is an
original implementation that works offline on synthetic data — no competitor
code, assets, or accounts were used.

## Feature map

| App | Signature feature | What this project now does | Implementation | Demo |
|---|---|---|---|---|
| **PocketGuard** | “In My Pocket” — one safe-to-spend number after bills | `safe_to_spend()` reserves upcoming recurring charges and divides the rest by days left | `expense/insights.py` | Smart Insights hero; ask *“How much can I spend safely?”* |
| **Safe Spend** | “Can I afford this?” verdict | `can_i_afford()` compares a purchase with the Safe-to-Spend amount and explains the gap | `expense/insights.py` | Smart Insights form; ask *“Can I afford Rs. 2,500?”* |
| **Rocket Money** | Subscription detection and cancellation prompts | Timing + amount-stability detection finds recurring charges, price hikes, and stale (“possibly cancelled”) charges | `expense/insights.py::detect_recurring` | Smart Insights → Subscription hunter |
| **Copilot Money** | Auto-categorisation that learns from corrections | Every saved transaction teaches a merchant→category rule; new entries get exact, fuzzy, then keyword suggestions | `expense/rules.py`, hooked into `expense/transactions.py` | Transactions → Add expense |
| **Copilot / Monarch** | Spending calendar / heatmap | 7-column month grid coloured by daily spend | `expense/insights.py::spending_calendar` | Smart Insights → Spending heatmap |
| **PocketSmith** | Cash-flow forecast | Month-end projection from the discretionary run rate + unbilled recurring charges | `expense/insights.py::month_forecast` | Smart Insights → Forecast gauge |
| **Simplifi** | Personalised spending plan that adjusts in real time | Forecast and Safe-to-Spend recalculate on every page load | `expense/insights.py` | Dashboard KPI + Smart Insights |
| **Monarch Money** | Weekly/monthly recap and goals | `monthly_recap()` writes a headline plus bullets; goals track progress and required monthly contribution | `expense/insights.py`, `expense/goals.py` | Smart Insights → Recap; Goals page |
| **YNAB** | Zero-based budgeting and sinking funds | Named goals with target dates, progress, on-track/behind status, and required monthly saving | `expense/goals.py` | Goals page |
| **YNAB / Monarch** | Debt payoff planner | Avalanche vs snowball simulation with total interest and payoff order | `expense/insights.py::debt_payoff` | Smart Insights → Debt payoff planner |
| **Fiscify / Origin** | Explainable financial health score | Weighted 0–100 score with five visible components and one next step | `expense/insights.py::financial_health` | Smart Insights → Financial health |
| **Cleo / Monarch** | Conversational finance assistant | Existing Grok agent now routes “safe to spend”, “afford”, “forecast”, “subscriptions”, “health”, “goals”, and “recap” intents to the new tools | `agent/agent.py`, `agent/prompts.py` | AI Assistant |

## How the algorithms work

### Safe to Spend
```
remaining      = monthly budget − spent
committed      = recurring charges whose next due date is today … month end
safe_to_spend  = max(remaining − committed, 0)
daily          = safe_to_spend / days_left
```
Status labels: `comfortable` (≥ Rs. 1,000/day), `tight` (< Rs. 1,000),
`critical` (< Rs. 300 or fully reserved), `no_budget`.

### Month-end forecast
```
discretionary_run_rate = (spent − recurring already posted) / days elapsed
projected              = recurring posted + upcoming recurring + run_rate × days left
```
Risk bands: >105% of budget = **over**, 95–105% = **watch**, otherwise **on track**.

### Subscription detection
Transactions are grouped by a normalised merchant key. Consecutive gaps are
classified as weekly, bi-weekly, monthly, quarterly, or yearly. A candidate needs
the minimum number of occurrences for its cadence, and confidence combines timing
consistency (45%+) and amount stability (20%+). The result carries next-due date,
monthly-equivalent cost, a price-hike flag (≥8% above average), and a stale flag
when a charge is overdue by more than 1.6× its cadence.

### Financial health score
| Component | Weight | Signal |
|---|---|---|
| Budget pace | 35 | Discretionary spend vs the expected pace at this point in the month |
| Category control | 20 | Share of category budgets within their limit |
| Recurring load | 15 | Recurring cost as a share of the monthly budget |
| Spending stability | 15 | This month vs the previous three-month average |
| Goal progress | 15 | Goals on track, behind, or absent |

The weakest weighted component becomes the single “next step”, so the score is
never a black box.

### Merchant learning
1. **Exact learned rule** — highest confidence, source says how many saves.
2. **Fuzzy learned rule** — Jaccard token overlap ≥ 0.5 across merchant keys.
3. **Keyword heuristic** — word-boundary match against a built-in merchant map.

The learner is wired into `add_transaction` and `update_transaction`, so a user
correction is the strongest signal and immediately improves the next suggestion.

### Debt payoff
Both strategies accrue monthly interest, pay minimums on every debt, then send
the extra payment to either the smallest balance (snowball) or the highest APR
(avalanche). The planner reports months, total interest, payoff order, and the
interest saved by the recommended strategy.

## Deliberate scope boundaries

These competitor features were **not** added because they need live bank data,
regulated advice, or paid third-party services:

- bank account aggregation / Plaid-style sync
- credit-score monitoring
- investment or tax advice
- actually cancelling a subscription
- multi-user households and shared budgets

The project remains a synthetic-data teaching demo, consistent with the
Assignment 2 safety requirement.

## Sources reviewed

- CNBC Select, *Best Budgeting Apps* (2026) — <https://www.cnbc.com/select/best-budgeting-apps>
- NerdWallet, *Best Budget Apps* (2026) — <https://www.nerdwallet.com/finance/learn/best-budget-apps>
- PocketGuard — <https://pocketguard.com>
- Rocket Money — <https://www.rocketmoney.com>
- Copilot Money — <https://copilot.money>
- Monarch Money — <https://www.monarchmoney.com>
- PocketSmith — <https://pocketsmith.com>
- YNAB — <https://www.ynab.com>
- Simplifi by Quicken — <https://www.quicken.com/simplifi>
- Safe Spend — <https://safespend.app>
- Origin — <https://useorigin.com>

Product names and trademarks belong to their respective owners. This document
records feature inspiration only.
