from __future__ import annotations

import pandas as pd
import streamlit as st


def page_analytics(jobs_df: pd.DataFrame) -> None:
    st.title("Analytics Dashboard")

    if jobs_df.empty:
        st.info("No jobs available for analytics.")
        return

    st.subheader("Most Common Strings")
    st.bar_chart(jobs_df["string_type"].value_counts())

    st.subheader("Tension Distribution")
    st.line_chart(jobs_df["tension_lbs"].value_counts().sort_index())

    st.subheader("Top Customers (by number of jobs)")
    st.bar_chart(jobs_df["customer_name"].value_counts().head(10))

    # st.subheader("Jobs Over Time")
    # df_time = jobs_df.copy()
    # df_time["created_at_dt"] = pd.to_datetime(df_time["created_at"], errors="coerce")
    # df_time = df_time.dropna(subset=["created_at_dt"])
    # df_time = df_time.groupby(df_time["created_at_dt"].dt.date).size()
    # st.area_chart(df_time)
