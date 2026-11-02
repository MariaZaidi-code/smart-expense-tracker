"""Monthly and category budget management page."""

from __future__ import annotations

from datetime import date

import streamlit as st

from expense.budgets import list_budgets, set_budget
from expense.transactions import list_categories
from ui.components import budget_progress, empty_state, format_money, page_header

month = date.today().strftime("%Y-%m")
budgets = list_budgets(month)
monthly = next((budget for budget in budgets if budget["category"] is None), None)
category_budgets = [budget for budget in budgets if budget["category"]]
categories = list_categories()

page_header(
    "Budgets",
    "Create realistic monthly limits and keep every category intentional.",
    "NOVEMBER PLAN",
)

if monthly:
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown("### Monthly budget")
            st.html(
                f"## {format_money(monthly['spent'])} "
                f"<span style='font-size:1rem;opacity:.7'>of {format_money(monthly['amount'])}</span>",
                
            )
            remaining_copy = (
                f"{format_money(monthly['remaining'])} remaining"
                if monthly["remaining"] >= 0
                else f"{format_money(abs(monthly['remaining']))} over budget"
            )
            st.caption(remaining_copy)
        with right:
            st.metric("Budget used", f"{monthly['percent']:.0f}%")
        st.progress(min(monthly["percent"] / 100, 1.0))
else:
    empty_state("No monthly budget", "Use the form below to create your monthly limit.")

form_col, info_col = st.columns([1, 1])
with form_col:
    with st.form("monthly_budget_form", border=True):
        st.markdown("#### Set monthly budget")
        monthly_amount = st.number_input(
            "Monthly limit (Rs.)",
            min_value=0.0,
            value=float(monthly["amount"]) if monthly else 0.0,
            step=1000.0,
        )
        if st.form_submit_button("Save monthly budget", width="stretch"):
            try:
                set_budget(month, monthly_amount)
                st.success("Monthly budget saved.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")

with info_col:
    with st.form("category_budget_form", border=True):
        st.markdown("#### Add or update category")
        category = st.selectbox("Category", categories)
        category_amount = st.number_input(
            "Category limit (Rs.)", min_value=0.0, step=500.0
        )
        if st.form_submit_button("Save category budget", width="stretch"):
            try:
                set_budget(month, category_amount, category)
                st.success(f"{category} budget saved.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")

st.markdown("### Category budgets")
if category_budgets:
    columns = st.columns(2)
    for index, budget in enumerate(category_budgets):
        with columns[index % 2]:
            with st.container(border=True):
                budget_progress(
                    budget["category"], budget["spent"], budget["amount"]
                )
else:
    empty_state(
        "No category budgets",
        "Add a category limit above to track spending progress.",
    )
