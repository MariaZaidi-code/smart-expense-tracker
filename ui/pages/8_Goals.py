"""Savings goals page (YNAB / Monarch style)."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from expense.goals import (
    add_to_goal,
    create_goal,
    delete_goal,
    goal_summary,
    list_goals,
)
from ui.components import (
    empty_state,
    format_money,
    goal_progress,
    kpi_card,
    page_header,
)

summary = goal_summary()
goals = summary["goals"]

page_header(
    "Goals",
    "Give every rupee a job. Track sinking funds, emergency savings, and big purchases in one place.",
    "SAVINGS GOALS",
)

columns = st.columns(3)
with columns[0]:
    kpi_card("Goals", str(summary["count"]), "Active savings targets")
with columns[1]:
    kpi_card(
        "Saved so far",
        format_money(summary["total_saved"]),
        f"{summary['progress_percent']}% of {format_money(summary['total_target'])}",
    )
with columns[2]:
    kpi_card(
        "Needs attention",
        str(len(summary["behind"])),
        "Goals behind schedule"
        if summary["behind"]
        else "Every goal is on track",
    )


@st.dialog("New savings goal")
def create_goal_dialog() -> None:
    with st.form("create_goal_form"):
        name = st.text_input("Goal name *", placeholder="e.g. Emergency fund")
        target = st.number_input(
            "Target amount (Rs.) *", min_value=0.0, value=50000.0, step=5000.0
        )
        saved = st.number_input(
            "Already saved (Rs.)", min_value=0.0, value=0.0, step=1000.0
        )
        target_date = st.date_input(
            "Target date",
            value=date.today() + timedelta(days=180),
        )
        category = st.selectbox(
            "Type",
            ["safety", "purchase", "travel", "education", "general"],
        )
        submitted = st.form_submit_button("Create goal", width="stretch")
        if submitted:
            try:
                create_goal(
                    name,
                    target,
                    saved,
                    target_date.isoformat(),
                    category,
                )
                st.success("Goal created.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")


@st.dialog("Add contribution")
def contribute_dialog(goal: dict) -> None:
    st.caption(
        f"{goal['name']} · {format_money(goal['saved_amount'])} of "
        f"{format_money(goal['target_amount'])} saved"
    )
    with st.form(f"contribute_{goal['id']}"):
        amount = st.number_input(
            "Contribution (Rs.)", min_value=0.0, value=1000.0, step=500.0
        )
        submitted = st.form_submit_button("Add to goal", width="stretch")
        if submitted:
            try:
                add_to_goal(goal["id"], amount)
                st.success("Contribution added.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")


action_left, action_right = st.columns([4, 1])
with action_left:
    st.markdown("### Your goals")
with action_right:
    if st.button("＋ New goal", width="stretch"):
        create_goal_dialog()

if not goals:
    empty_state(
        "No goals yet",
        "Create an emergency fund first — three to six months of essential expenses is the usual target.",
    )
else:
    for goal in goals:
        goal_progress(goal)
        meta, contribute_col, delete_col = st.columns([2.4, 1, 1])
        with meta:
            target_text = (
                f"Target {goal['target_date']}" if goal.get("target_date") else "No target date"
            )
            st.caption(
                f"{goal['category'].title()} · {target_text} · "
                f"{format_money(goal['remaining'])} remaining"
            )
        with contribute_col:
            if st.button(
                "Add money",
                key=f"contribute_{goal['id']}",
                width="stretch",
                disabled=goal["status"] == "achieved",
            ):
                contribute_dialog(goal)
        with delete_col:
            if st.button("Delete", key=f"delete_{goal['id']}", width="stretch"):
                try:
                    delete_goal(goal["id"])
                    st.success(f"Deleted {goal['name']}.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

st.markdown("---")
st.caption(
    "A goal marked **behind** has saved less than the straight-line pace toward its target date. "
    "Move the date or add a contribution to get back on track."
)
