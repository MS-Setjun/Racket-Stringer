from __future__ import annotations

import pandas as pd
import streamlit as st


def page_analytics(jobs_df: pd.DataFrame) -> None:
    st.title("Analytics Dashboard")

    jobs_df = jobs_df[jobs_df["customer_name"] != "No String"]

    if jobs_df.empty:
        st.info("No jobs available for analytics.")
        return

    st.subheader("Most Common Strings")
    st.bar_chart(jobs_df["string_type"].value_counts())

    st.subheader("Tension Distribution")
    st.line_chart(jobs_df["tension_lbs"].value_counts().sort_index())

    st.subheader("Top Customers (by number of jobs)")
    st.bar_chart(jobs_df["customer_name"].value_counts().head(10))