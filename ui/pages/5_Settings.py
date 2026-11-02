"""Simple application preferences page."""

import streamlit as st

from ui.components import page_header

page_header(
    "Settings",
    "Manage display and demonstration preferences for this local app.",
    "PREFERENCES",
)

with st.container(border=True):
    st.markdown("### Display")
    st.selectbox("Currency", ["Pakistani Rupees (Rs.)"], disabled=True)
    st.toggle("Compact transaction rows", value=False)
    st.toggle("Show synthetic-data reminder", value=True)

with st.container(border=True):
    st.markdown("### Demo data")
    st.caption(
        "This assignment uses synthetic transactions only. No bank account or "
        "real financial credential is connected."
    )
    st.button("Reset demo preferences")
