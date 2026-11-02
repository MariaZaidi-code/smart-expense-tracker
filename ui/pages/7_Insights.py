"""Smart insights page: the features that make leading budgeting apps stand out.

* Safe to Spend (PocketGuard / Safe Spend)
* Month-end forecast (PocketSmith / Simplifi)
* Subscription hunter (Rocket Money / Copilot)
* Explainable financial health score (Fiscify / Origin)
* Monthly recap (Monarch)
* Spending heatmap (Copilot)
* Debt payoff planner (YNAB / Monarch)
"""

from __future__ import annotations

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from expense.insights import (
    can_i_afford,
    debt_payoff,
    financial_health,
    month_forecast,
    monthly_recap,
    safe_to_spend,
    spending_calendar,
    subscription_summary,
)
from ui.components import (
    empty_state,
    format_money,
    kpi_card,
    page_header,
    safe_to_spend_card,
    score_bar,
)
from ui.theme import (
    GRID,
    MUTED,
    OVER_BUDGET,
    PRIMARY,
    PRIMARY_FADE,
    TEXT_MAIN,
    TEXT_MUTED,
    chart_layout,
)

month = date.today().strftime("%Y-%m")

page_header(
    "Smart insights",
    "One trustworthy number, an early-warning forecast, and the subscriptions quietly draining your budget.",
    "INTELLIGENCE LAYER",
)

try:
    snapshot = safe_to_spend(month)
    forecast = month_forecast(month)
    health = financial_health(month)
    subscriptions = subscription_summary()
    recap = monthly_recap(month)
    calendar_rows = spending_calendar(month)
except Exception as error:  # keep the page usable on a half-seeded database
    st.error(f"Insights are unavailable: {error}")
    st.stop()

# ---------------------------------------------------------------------------
# Safe to spend
# ---------------------------------------------------------------------------
safe_to_spend_card(snapshot)

kpi_columns = st.columns(3)
with kpi_columns[0]:
    kpi_card(
        "Budget left",
        format_money(snapshot["remaining"]),
        f"Of {format_money(snapshot['budget'])} monthly budget",
    )
with kpi_columns[1]:
    kpi_card(
        "Reserved for bills",
        format_money(snapshot["upcoming_commitments"]),
        "Recurring charges still due this month",
    )
with kpi_columns[2]:
    kpi_card(
        "Daily allowance",
        format_money(snapshot["per_day"]),
        f"For the next {int(snapshot['days_left'])} days",
    )

# ---------------------------------------------------------------------------
# Forecast + health
# ---------------------------------------------------------------------------
st.html("---")
forecast_col, health_col = st.columns([0.9, 1.1])

with forecast_col:
    st.subheader("Month-end forecast")
    risk_colour = {
        "over": OVER_BUDGET,
        "watch": MUTED,
        "on_track": PRIMARY,
        "unknown": MUTED,
    }.get(forecast["risk"], MUTED)
    figure = go.Figure(
        go.Indicator(
            mode="number+gauge",
            value=forecast["projected_total"],
            number={"prefix": "Rs. ", "font": {"color": TEXT_MAIN, "size": 30}},
            gauge={
                "axis": {
                    "range": [0, max(forecast["budget"], forecast["projected_total"]) * 1.1],
                    "tickformat": "~s",
                    "tickfont": {"color": TEXT_MUTED, "size": 9},
                },
                "bar": {"color": risk_colour},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {
                        "range": [0, forecast["budget"]],
                        "color": "rgba(163,167,246,0.10)",
                    }
                ],
                "threshold": {
                    "line": {"color": TEXT_MAIN, "width": 3},
                    "thickness": 0.8,
                    "value": forecast["budget"],
                },
            },
            domain={"x": [0, 1], "y": [0.35, 1]},
        )
    )
    figure.update_layout(**chart_layout(height=210))
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    st.markdown(
        f"**{forecast['label']}** — projected at {format_money(forecast['projected_total'])} "
        f"against a {format_money(forecast['budget'])} budget."
    )
    difference = forecast["projected_over"]
    if forecast["budget"]:
        if difference > 0:
            st.caption(f"Trend is {format_money(difference)} over budget at the current run rate.")
        else:
            st.caption(f"Trend is {format_money(abs(difference))} under budget at the current run rate.")
    st.caption(
        f"{format_money(forecast['daily_run_rate'])}/day discretionary run rate · "
        f"{int(forecast['days_left'])} days left"
    )

with health_col:
    st.subheader("Financial health")
    grade_colour = PRIMARY if health["score"] >= 70 else MUTED if health["score"] >= 55 else OVER_BUDGET
    score_left, score_right = st.columns([0.36, 0.64])
    with score_left:
        score_figure = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=health["score"],
                number={"font": {"color": TEXT_MAIN, "size": 40}, "suffix": ""},
                gauge={
                    "axis": {"range": [0, 100], "tickfont": {"color": TEXT_MUTED, "size": 9}},
                    "bar": {"color": grade_colour},
                    "bgcolor": "rgba(0,0,0,0)",
                    "borderwidth": 0,
                    "steps": [{"range": [0, 100], "color": "rgba(163,167,246,0.10)"}],
                },
                domain={"x": [0, 1], "y": [0, 1]},
            )
        )
        score_figure.update_layout(**chart_layout(height=190))
        st.plotly_chart(score_figure, width="stretch", config={"displayModeBar": False})
        st.markdown(f"<center><h3>Grade {health['grade']}</h3></center>")
    with score_right:
        st.caption(
            f"Focus area: **{health['focus_area']}**. {health['next_step']}"
        )
        for component in health["components"]:
            score_bar(
                component["label"],
                component["score"],
                component["detail"],
                component["advice"] if component["score"] < 70 else "",
            )

# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("Subscription hunter")
sub_columns = st.columns(3)
with sub_columns[0]:
    kpi_card(
        "Active recurring",
        str(subscriptions["count"]),
        "Bills and subscriptions detected",
    )
with sub_columns[1]:
    kpi_card(
        "Monthly recurring",
        format_money(subscriptions["monthly_total"]),
        f"{format_money(subscriptions['annual_total'])} per year",
    )
with sub_columns[2]:
    kpi_card(
        "Price hikes / stale",
        f"{len(subscriptions['price_hikes'])} / {len(subscriptions['canceled'])}",
        "Review before the next charge",
    )

if subscriptions["items"]:
    st.dataframe(
        [
            {
                "Merchant": item["description"],
                "Cadence": item["cadence"].title(),
                "Monthly cost": format_money(item["monthly_cost"]),
                "Last charge": item["last_charged"],
                "Next due": item["next_due"],
                "Confidence": f"{item['confidence']:.0f}%",
                "Status": item["status"].title(),
            }
            for item in subscriptions["items"]
        ],
        width="stretch",
        hide_index=True,
    )
    if subscriptions["price_hikes"]:
        for item in subscriptions["price_hikes"]:
            st.warning(
                f"**{item['description']}** rose {item['price_change_percent']:+.0f}% "
                f"to {format_money(item['last_amount'])}. Check whether the upgrade is worth it.",
                icon="📈",
            )
    if subscriptions["canceled"]:
        with st.expander(f"Possibly cancelled ({len(subscriptions['canceled'])})"):
            for item in subscriptions["canceled"]:
                st.caption(
                    f"{item['description']} · last charged {item['last_charged']} · "
                    f"{format_money(item['last_amount'])} · no charge since its usual cadence."
                )
else:
    empty_state(
        "No recurring charges detected",
        "Add at least three months of transactions for the detector to find subscriptions and bills.",
    )

# ---------------------------------------------------------------------------
# Heatmap + recap
# ---------------------------------------------------------------------------
st.markdown("---")
heat_col, recap_col = st.columns([1.15, 0.85])

with heat_col:
    st.subheader("Spending heatmap")
    weeks = max(row["week"] for row in calendar_rows) + 1
    values = [[None] * 7 for _ in range(weeks)]
    labels = [[""] * 7 for _ in range(weeks)]
    for row in calendar_rows:
        values[row["week"]][row["weekday"]] = row["amount"]
        labels[row["week"]][row["weekday"]] = str(row["day"])
    figure = go.Figure(
        go.Heatmap(
            z=values,
            x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            y=[f"Week {index + 1}" for index in range(weeks)],
            text=labels,
            texttemplate="%{text}",
            textfont={"size": 10, "color": TEXT_MAIN},
            colorscale=[[0, "rgba(95,96,103,0.18)"], [1, PRIMARY]],
            showscale=False,
            xgap=4,
            ygap=4,
            hovertemplate="Day %{text}<br><b>Rs. %{z:,.0f}</b><extra></extra>",
        )
    )
    figure.update_layout(**chart_layout(height=300))
    figure.update_xaxes(side="top", showgrid=False)
    figure.update_yaxes(showgrid=False, autorange="reversed")
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    st.caption(f"Darker cells mean a heavier spending day in {month}.")

with recap_col:
    st.subheader("Monthly recap")
    st.markdown(f"**{recap['headline']}**")
    for bullet in recap["bullets"]:
        st.markdown(f"- {bullet}")
    st.caption(f"Recap generated from {recap['month']} transaction data.")

# ---------------------------------------------------------------------------
# Affordability + debt planner
# ---------------------------------------------------------------------------
st.markdown("---")
afford_col, debt_col = st.columns([0.8, 1.2])

with afford_col:
    st.subheader("Can I afford this?")
    with st.form("afford_form"):
        purchase = st.number_input(
            "Purchase amount (Rs.)", min_value=0.0, value=2500.0, step=500.0
        )
        checked = st.form_submit_button("Check against Safe to Spend", width="stretch")
    if checked:
        try:
            verdict = can_i_afford(purchase, month)
            if verdict["affordable"]:
                st.success(verdict["message"], icon="✅")
            else:
                st.error(verdict["message"], icon="🛑")
            st.caption(
                f"Safe to spend: {format_money(verdict['safe_to_spend'])} · "
                f"After purchase: {format_money(verdict['remaining_after'])}"
            )
        except ValueError as error:
            st.error(str(error))

with debt_col:
    st.subheader("Debt payoff planner")
    st.caption(
        "Compare avalanche (highest interest first) with snowball (smallest balance first)."
    )
    with st.expander("Open the planner", expanded=False):
        with st.form("debt_form"):
            debt_one, debt_two = st.columns(2)
            with debt_one:
                name_a = st.text_input("Debt 1 name", value="Credit card")
                balance_a = st.number_input(
                    "Debt 1 balance (Rs.)", min_value=0.0, value=120000.0, step=5000.0
                )
                apr_a = st.number_input(
                    "Debt 1 APR (%)", min_value=0.0, value=24.0, step=1.0
                )
                minimum_a = st.number_input(
                    "Debt 1 minimum (Rs.)", min_value=0.0, value=6000.0, step=500.0
                )
            with debt_two:
                name_b = st.text_input("Debt 2 name", value="Personal loan")
                balance_b = st.number_input(
                    "Debt 2 balance (Rs.)", min_value=0.0, value=300000.0, step=5000.0
                )
                apr_b = st.number_input(
                    "Debt 2 APR (%)", min_value=0.0, value=12.0, step=1.0
                )
                minimum_b = st.number_input(
                    "Debt 2 minimum (Rs.)", min_value=0.0, value=12000.0, step=500.0
                )
            extra = st.number_input(
                "Extra payment per month (Rs.)", min_value=0.0, value=5000.0, step=500.0
            )
            planned = st.form_submit_button("Build payoff plan", width="stretch")
        if planned:
            debts = [
                {
                    "name": name_a or "Debt 1",
                    "balance": balance_a,
                    "apr": apr_a,
                    "min_payment": minimum_a,
                },
                {
                    "name": name_b or "Debt 2",
                    "balance": balance_b,
                    "apr": apr_b,
                    "min_payment": minimum_b,
                },
            ]
            try:
                plan = debt_payoff(debts, extra_payment=extra)
                st.success(plan["summary"], icon="🎯")
                comparison = st.columns(2)
                for column, key in zip(comparison, ("avalanche", "snowball")):
                    with column:
                        result = plan[key]
                        st.metric(
                            key.title(),
                            f"{result['months']} months",
                            f"{format_money(result['total_interest'])} interest",
                        )
                st.caption(
                    "Payoff order: " + " → ".join(plan[plan["recommended"]]["payoff_order"])
                )
            except ValueError as error:
                st.error(str(error))
