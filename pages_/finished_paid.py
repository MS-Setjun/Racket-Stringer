from __future__ import annotations

import pandas as pd
import streamlit as st

from pages_.common import JOB_STATUSES, STATUS_IN_PROGRESS, esc, safe_index, save_jobs


def page_finished_paid(jobs_df: pd.DataFrame) -> pd.DataFrame:
    st.title("Finished & Paid Jobs")

    finished = jobs_df[jobs_df["status"] != STATUS_IN_PROGRESS].copy()

    if finished.empty:
        st.info("No finished jobs.")
        return jobs_df

    finished["created_at_dt"] = pd.to_datetime(
        finished["created_at"], errors="coerce"
    )
    finished = finished.sort_values(
        "created_at_dt", ascending=False, na_position="last"
    )

    name_filter = st.text_input("Filter by name")

    if name_filter:
        finished = finished[
            finished["customer_name"].str.contains(name_filter, case=False)
        ]

    st.subheader("Jobs")

    for _, row in finished.iterrows():
        st.markdown(
            f"""
            <div style="padding:10px 0; border-bottom:1px solid #ddd;">
                <strong>Job #{row['job_id']} – {esc(row['customer_name'])}</strong><br>
                {esc(row['string_type'])} @ {row['tension_lbs']} lbs<br>
                Created: {esc(row['created_at'])}<br>
                Completed: {esc(row['completed_at'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander(f"Edit Job #{row['job_id']}"):
            status = st.selectbox(
                "Status",
                JOB_STATUSES,
                index=safe_index(JOB_STATUSES, row["status"]),
                key=f"status_fin_{row['job_id']}",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Save", key=f"save_fin_{row['job_id']}"):
                    jobs_df.loc[
                        jobs_df["job_id"] == row["job_id"], "status"
                    ] = status
                    save_jobs(jobs_df)
                    st.success("Updated.")
                    st.rerun()

            with col2:
                if st.button("Delete", key=f"del_{row['job_id']}"):
                    jobs_df = jobs_df[jobs_df["job_id"] != row["job_id"]]
                    save_jobs(jobs_df)
                    st.warning("Deleted.")
                    st.rerun()

    return jobs_df