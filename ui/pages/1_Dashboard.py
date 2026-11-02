"""Dashboard page."""

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from expense.analytics import (
    budget_status,
    category_breakdown,
    month_summary,
    spending_trend,
    unusual_spending,
)
from expense.transactions import list_transactions
from ui.components import (
    alert_banner,
    budget_progress,
    empty_state,
    format_money,
    hero_card,
    kpi_card,
    page_header,
    recent_transaction_list,
)
from ui.theme import (
    CHART_COLORS,
    GRID,
    MUTED,
    OVER_BUDGET,
    PRIMARY,
    PRIMARY_FADE,
    TEXT_MAIN,
    chart_layout,
)

month = date.today().strftime("%Y-%m")
summary = month_summary(month)
categories = category_breakdown(month)
trend = spending_trend(month)
budgets = budget_status(month)
alerts = unusual_spending(month)
recent = list_transactions()[:5]

page_header(
    "Good evening, Rameen",
    "A clear view of your spending, budgets, and unusual activity this month.",
    "NOVEMBER OVERVIEW",
)

change = summary["month_change_percent"]
hero_card(summary["remaining"], -change)

columns = st.columns(3)
details = [
    ("Spent this month", format_money(summary["total_spent"]), "Across all recorded categories"),
    ("Total budget", format_money(summary["total_budget"]), "Monthly spending limit"),
    (
        "Vs. last month",
        f"{change:+.1f}%",
        "Lower is better" if change <= 0 else "Spending has increased",
    ),
]
for column, values in zip(columns, details):
    with column:
        kpi_card(*values)

chart_left, chart_right = st.columns([1.35, 0.85])
with chart_left:
    st.subheader("Spending activity")
    if trend:
        amounts = [row["amount"] for row in trend]
        colors = [MUTED] * len(trend)
        colors[-1] = OVER_BUDGET
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[row["date"] for row in trend],
                y=amounts,
                mode="lines",
                line=dict(color=PRIMARY, width=3, shape="spline"),
                fill="tozeroy",
                fillcolor=PRIMARY_FADE,
                hoverinfo="skip",
            )
        )
        figure.add_trace(
            go.Bar(
                x=[row["date"] for row in trend],
                y=amounts,
                marker=dict(color=colors, line=dict(width=0)),
                width=0.58,
                hovertemplate="%{x}<br><b>Rs. %{y:,.0f}</b><extra></extra>",
            ),
        )
        figure.add_trace(
            go.Scatter(
                x=[[row["date"] for row in trend][-1]],
                y=[amounts[-1]],
                mode="markers",
                marker=dict(color=OVER_BUDGET, size=11, line=dict(color=TEXT_MAIN, width=2)),
                hoverinfo="skip",
            )
        )
        figure.update_layout(**chart_layout())
        figure.update_layout(
            bargap=0.35,
            barcornerradius=12,
            showlegend=False,
        )
        figure.update_xaxes(showgrid=False, linecolor=MUTED, tickfont=dict(color=MUTED))
        figure.update_yaxes(
            gridcolor=GRID,
            griddash="dash",
            tickprefix="Rs. ",
            linecolor=MUTED,
            tickfont=dict(color=MUTED),
        )
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    else:
        empty_state("No activity yet", "Daily spending will appear here after expenses are added.")

with chart_right:
    st.subheader("Category breakdown")
    if categories:
        figure = go.Figure(
            go.Pie(
                labels=[row["category"] for row in categories],
                values=[row["amount"] for row in categories],
                hole=0.7,
                marker=dict(colors=CHART_COLORS, line=dict(color=MUTED, width=2)),
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>Rs. %{value:,.0f}<extra></extra>",
            )
        )
        figure.update_layout(**chart_layout())
        figure.add_annotation(
            text=f"<b>{format_money(summary['total_spent'])}</b><br><span style='font-size:10px'>TOTAL</span>",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=TEXT_MAIN, size=14),
        )
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
    else:
        empty_state("No spending yet", "Add your first expense to see a category breakdown.")

left, right = st.columns([1.15, 0.85])
with left:
    st.subheader("Budget progress")
    if budgets:
        for budget in budgets:
            budget_progress(budget["category"], budget["spent"], budget["amount"])
    else:
        empty_state("No category budgets", "Visit Budgets to set your first category limit.")

with right:
    st.subheader("Unusual spending")
    if alerts:
        for alert in alerts:
            alert_banner(alert["category"], alert["reason"])
    else:
        st.markdown(
            '<div class="surface-card" style="padding:1.1rem"><strong>✓ No unusual activity</strong><p style="margin:.4rem 0 0">Your categories are within their recent patterns.</p></div>',
            unsafe_allow_html=True,
        )

st.subheader("Recent transactions")
if recent:
    recent_transaction_list(recent)
else:
    empty_state("No transactions", "Add a synthetic expense to populate your dashboard.")
