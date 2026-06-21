from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from pages_.common import (
    STATUS_COMPLETED_PAID,
    STATUS_COMPLETED_UNPAID,
    STATUS_IN_PROGRESS,
    JOB_STATUSES,
    esc,
    safe_index,
    save_jobs,
)


def page_dashboard(jobs_df: pd.DataFrame, strings_df: pd.DataFrame) -> pd.DataFrame:
    st.title("Dashboard")
    col_a, col_b = st.columns(2, gap="large", use_container_width=True)

    string_options = strings_df["string_type"].tolist()

    # ---------------- In Progress ----------------
    with col_a:
        st.subheader("In Progress Jobs")
        in_progress = jobs_df[jobs_df["status"] == STATUS_IN_PROGRESS]

        for _, row in in_progress.iterrows():
            with st.expander(f"Job #{row['job_id']} – {esc(row['customer_name'])}"):
                string_choice = st.selectbox(
                    "String",
                    string_options,
                    index=safe_index(string_options, row["string_type"]),
                    key=f"string_{row['job_id']}",
                )

                tension = st.slider(
                    "Tension (lbs)",
                    18,
                    34,
                    int(row["tension_lbs"]),
                    1,
                    key=f"tension_{row['job_id']}",
                )

                status = st.selectbox(
                    "Status",
                    JOB_STATUSES,
                    index=safe_index(JOB_STATUSES, row["status"]),
                    key=f"status_{row['job_id']}",
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Save", key=f"save_{row['job_id']}"):
                        jobs_df.loc[
                            jobs_df["job_id"] == row["job_id"],
                            ["string_type", "tension_lbs", "status"],
                        ] = [string_choice, tension, status]

                        if status.startswith("Completed"):
                            jobs_df.loc[
                                jobs_df["job_id"] == row["job_id"], "completed_at"
                            ] = datetime.now().isoformat()

                        save_jobs(jobs_df)
                        st.success("Updated.")
                        st.rerun()

                with col2:
                    if st.button("Delete Job", key=f"delete_{row['job_id']}"):
                        jobs_df = jobs_df[jobs_df["job_id"] != row["job_id"]]
                        save_jobs(jobs_df)
                        st.warning(f"Job #{row['job_id']} deleted.")
                        st.rerun()

    # ---------------- Completed – Unpaid ----------------
    with col_b:
        st.subheader("Completed – Unpaid")
        unpaid = jobs_df[jobs_df["status"] == STATUS_COMPLETED_UNPAID]

        for _, row in unpaid.iterrows():

            # subtle divider
            st.markdown("<hr style='margin:6px 0; opacity:0.25;'>", unsafe_allow_html=True)

            left, right = st.columns([4, 1])

            with left:
                st.markdown(
                    f"""
                    <div style="line-height:1.4;">
                        <strong>🏸 Job #{row['job_id']} – {esc(row['customer_name'])}</strong><br>
                        {esc(row['string_type'])} @ {row['tension_lbs']} lbs
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with right:
                if st.button("💰 Mark Paid", key=f"paid_{row['job_id']}"):
                    jobs_df.loc[
                        jobs_df["job_id"] == row["job_id"], "status"
                    ] = STATUS_COMPLETED_PAID
                    save_jobs(jobs_df)
                    st.success("✔️ Marked paid.")
                    st.rerun()

    return jobs_df
