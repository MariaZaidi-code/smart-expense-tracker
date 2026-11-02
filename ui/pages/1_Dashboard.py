"""Dashboard page matching the design spec."""

from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from expense.analytics import budget_status, category_breakdown, month_summary, spending_trend
from expense.insights import financial_health, safe_to_spend
from expense.transactions import list_transactions
from ui.theme import PRIMARY, TEXT_MAIN, TEXT_MUTED, chart_layout


def _money(value: float) -> str:
    return f"Rs. {value:,.0f}"


month = date.today().strftime("%Y-%m")
summary = month_summary(month)
categories = category_breakdown(month)
trend = spending_trend(month)
budgets = budget_status(month)
recent = list_transactions()[:5]
safe = safe_to_spend(month)
health = financial_health(month)

# Page header
left, right = st.columns([4, 1])
with left:
    st.markdown("## Dashboard")
    st.caption("Your personal finance overview")
with right:
    st.markdown(
        "<div style='text-align:right;padding-top:.5rem;'><span style='background:rgba(34,197,94,.12);color:#22C55E;padding:.3rem .7rem;border-radius:999px;font-size:.75rem;font-weight:700;'>Grok connected</span></div>",
        unsafe_allow_html=True,
    )

# Hero card
st.markdown(
    f"""
    <div style='background:linear-gradient(135deg,#2F6BFF,#6D5BFF);border-radius:1rem;padding:1.5rem;color:#fff;margin-bottom:1rem;position:relative;overflow:hidden;'>
        <div style='font-size:.78rem;font-weight:700;opacity:.8;text-transform:uppercase;letter-spacing:.12em;'>Remaining Budget</div>
        <div style='font-size:clamp(2rem,4vw,3.2rem);font-weight:800;font-variant-numeric:tabular-nums;margin:.4rem 0;'>{_money(summary['remaining'])}</div>
        <span style='background:rgba(239,68,68,.18);color:#FCA5A5;padding:.3rem .7rem;border-radius:999px;font-size:.75rem;font-weight:700;'>↓ {abs(summary['month_change_percent']):.1f}% lower than last month</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# 4 KPI cards
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Safe to Spend</div><div class='kpi-value'>{_money(safe['safe_to_spend'])}</div><div class='kpi-detail'>{_money(safe['per_day'])}/day</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Spent This Month</div><div class='kpi-value'>{_money(summary['total_spent'])}</div><div class='kpi-detail'>Across all categories</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Total Budget</div><div class='kpi-value'>{_money(summary['total_budget'])}</div><div class='kpi-detail'>Monthly limit</div></div>", unsafe_allow_html=True)
with k4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Vs. Last Month</div><div class='kpi-value'>{summary['month_change_percent']:+.1f}%</div><div class='kpi-detail'>{'Spending increased' if summary['month_change_percent'] > 0 else 'Spending decreased'}</div></div>", unsafe_allow_html=True)

st.markdown("---")

# Charts
cl, cr = st.columns([2, 1])
with cl:
    st.subheader("Spending Activity")
    if trend:
        dates = pd.to_datetime([r["date"] for r in trend])
        values = [r["amount"] for r in trend]
        colors = ["#4E5459"] * len(trend)
        if colors:
            colors[-1] = "#EF4444"
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dates, y=values, marker=dict(color=colors, line=dict(width=0)), width=0.6))
        fig.add_trace(go.Scatter(x=dates, y=values, mode="lines", line=dict(color=PRIMARY, width=2)))
        fig.update_layout(**chart_layout())
        fig.update_yaxes(tickprefix="Rs. ", gridcolor="rgba(30,42,68,.7)", griddash="dash")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No spending activity yet.")
with cr:
    st.subheader("Category Breakdown")
    if categories:
        labels = [r["category"] for r in categories]
        values = [r["amount"] for r in categories]
        fig2 = px.pie(names=labels, values=values, hole=0.65, color_discrete_sequence=[PRIMARY, "#F59E0B", "#4E5459", "#8A94A8", "#22C55E"])
        fig2.update_layout(**chart_layout())
        fig2.add_annotation(text=f"<b>{_money(summary['total_spent'])}</b><br><span style='font-size:10px'>Total</span>", x=0.5, y=0.5, showarrow=False, font=dict(color=TEXT_MAIN, size=14))
        st.plotly_chart(fig2, use_container_width=True)
        for r in categories:
            pct = r["amount"] / summary["total_spent"] * 100 if summary["total_spent"] else 0
            st.caption(f"{r['category']}: {pct:.0f}%")
    else:
        st.info("No category data yet.")

st.markdown("---")

# Recent transactions + quick actions
ct, ca = st.columns([2, 1])
with ct:
    st.subheader("Recent Transactions")
    if recent:
        data = {
            "Date": [r["transaction_date"] for r in recent],
            "Description": [r["description"] for r in recent],
            "Category": [r["category"] for r in recent],
            "Amount": [_money(r["amount"]) for r in recent],
            "Payment": [r["payment_method"] for r in recent],
        }
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    else:
        st.info("No recent transactions.")
with ca:
    st.subheader("Quick Actions")
    st.button("Add Expense", use_container_width=True)
    st.button("Add Budget", use_container_width=True)
    st.button("Add Goal", use_container_width=True)
    st.markdown("---")
    st.subheader("Budget Status")
    if summary["total_budget"]:
        progress = min(summary["total_spent"] / summary["total_budget"], 1.0)
        st.progress(progress)
        st.caption(f"Monthly Budget: {_money(summary['total_budget'])} ({progress*100:.0f}% spent)")
    else:
        st.caption("No monthly budget set.")
