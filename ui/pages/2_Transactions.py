"""Searchable transaction management page."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from expense.rules import suggest_category
from expense.transactions import (
    add_transaction,
    delete_transaction,
    list_categories,
    list_transactions,
    update_transaction,
)
from ui.components import empty_state, format_money, page_header

categories = list_categories()


@st.dialog("Add expense")
def add_expense_dialog() -> None:
    st.caption(
        "Record a synthetic transaction. The category is suggested from merchants "
        "you have already categorised."
    )
    description = st.text_input("Description *", placeholder="e.g. Lahore Kitchen")
    suggestion = suggest_category(description) if description.strip() else None
    options = ["Select a category", *categories]
    default_index = 0
    if suggestion and suggestion.get("category") in categories:
        default_index = options.index(suggestion["category"])
        st.caption(
            f"✨ Suggested **{suggestion['category']}** — {suggestion['source']} "
            f"({float(suggestion.get('confidence', 0)) * 100:.0f}% confidence)."
        )
    category = st.selectbox(
        "Category *",
        options,
        index=default_index,
        key=f"add_category::{description.strip().lower()[:40]}",
    )
    amount = st.number_input("Amount (Rs.) *", min_value=0.0, step=100.0)
    transaction_date = st.date_input("Date *", value=date.today())
    payment = st.selectbox("Payment method", ["Card", "Cash", "Bank transfer"])
    notes = st.text_area("Notes", placeholder="Optional context")
    if st.button("Save expense", width="stretch"):
        errors = []
        if not description.strip():
            errors.append("Description is required.")
        if amount <= 0:
            errors.append("Amount must be greater than Rs. 0.")
        if category == "Select a category":
            errors.append("Select a category.")
        if errors:
            for error in errors:
                st.error(error, icon="⚠️")
        else:
            try:
                add_transaction(
                    description,
                    amount,
                    category,
                    transaction_date.isoformat(),
                    payment,
                    notes,
                )
                st.success("Expense added. The merchant is now remembered for next time.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")


@st.dialog("Edit expense")
def edit_expense_dialog(transaction: dict) -> None:
    with st.form(f"edit_{transaction['id']}"):
        description = st.text_input("Description *", value=transaction["description"])
        amount = st.number_input(
            "Amount (Rs.) *", min_value=0.0, value=float(transaction["amount"]), step=100.0
        )
        category = st.selectbox(
            "Category *",
            categories,
            index=categories.index(transaction["category"]),
        )
        transaction_date = st.date_input(
            "Date *", value=date.fromisoformat(transaction["transaction_date"])
        )
        payment_options = ["Card", "Cash", "Bank transfer"]
        payment = st.selectbox(
            "Payment method",
            payment_options,
            index=payment_options.index(transaction["payment_method"])
            if transaction["payment_method"] in payment_options
            else 0,
        )
        notes = st.text_area("Notes", value=transaction["notes"])
        submitted = st.form_submit_button("Update expense", width="stretch")
        if submitted:
            try:
                update_transaction(
                    transaction["id"],
                    description,
                    amount,
                    category,
                    transaction_date.isoformat(),
                    payment,
                    notes,
                )
                st.success("Expense updated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error), icon="⚠️")


page_header(
    "Transactions",
    "Search, filter, sort, and maintain your synthetic expense records.",
    "EXPENSE LEDGER",
)

action_left, action_right = st.columns([4, 1])
with action_right:
    if st.button("＋ Add expense", width="stretch"):
        add_expense_dialog()

with st.container(border=True):
    st.markdown("#### Find transactions")
    search_col, category_col, sort_col = st.columns([1.4, 1, 1])
    with search_col:
        search = st.text_input("Search", placeholder="Merchant or category", label_visibility="collapsed")
    with category_col:
        category_filter = st.selectbox(
            "Category filter", ["All categories", *categories], label_visibility="collapsed"
        )
    with sort_col:
        sort_label = st.selectbox(
            "Sort",
            ["Newest first", "Oldest first", "Amount: high to low", "Amount: low to high"],
            label_visibility="collapsed",
        )

    range_col, min_col, max_col = st.columns([1.4, 1, 1])
    with range_col:
        date_range = st.date_input(
            "Date range",
            value=(date.today() - timedelta(days=90), date.today()),
        )
    with min_col:
        min_amount = st.number_input("Minimum amount", min_value=0.0, step=500.0)
    with max_col:
        max_amount = st.number_input("Maximum amount", min_value=0.0, step=500.0)

sort_map = {
    "Newest first": "newest",
    "Oldest first": "oldest",
    "Amount: high to low": "amount_high",
    "Amount: low to high": "amount_low",
}
start_date = date_range[0].isoformat() if len(date_range) == 2 else None
end_date = date_range[1].isoformat() if len(date_range) == 2 else None
rows = list_transactions(
    search=search,
    category=None if category_filter == "All categories" else category_filter,
    start_date=start_date,
    end_date=end_date,
    min_amount=min_amount if min_amount > 0 else None,
    max_amount=max_amount if max_amount > 0 else None,
    sort=sort_map[sort_label],
)

st.markdown(f"#### {len(rows)} transaction{'s' if len(rows) != 1 else ''}")
if rows:
    import csv, io
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Description", "Category", "Date", "Payment", "Amount"])
    for row in rows:
        writer.writerow([row["description"], row["category"], row["transaction_date"], row["payment_method"], row["amount"]])
    st.download_button("Download CSV", data=buffer.getvalue(), file_name="transactions.csv", mime="text/csv")
    st.dataframe(
        [
            {
                "Description": row["description"],
                "Category": row["category"],
                "Date": row["transaction_date"],
                "Payment": row["payment_method"],
                "Amount": format_money(row["amount"]),
            }
            for row in rows
        ],
        width="stretch",
        hide_index=True,
    )

    manage_left, edit_col, delete_col = st.columns([2, 1, 1])
    with manage_left:
        selected_id = st.selectbox(
            "Manage a transaction",
            [row["id"] for row in rows],
            format_func=lambda item_id: next(
                f"{row['description']} · {format_money(row['amount'])}"
                for row in rows
                if row["id"] == item_id
            ),
        )
    selected = next(row for row in rows if row["id"] == selected_id)
    with edit_col:
        st.write("")
        if st.button("Edit selected", width="stretch"):
            edit_expense_dialog(selected)
    with delete_col:
        st.write("")
        if st.button("Delete selected", width="stretch"):
            try:
                delete_transaction(selected_id)
                st.success("Transaction deleted.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
else:
    empty_state(
        "No matching transactions",
        "Adjust the filters or add a new synthetic expense.",
    )
