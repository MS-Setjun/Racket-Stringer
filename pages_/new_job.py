from __future__ import annotations

from datetime import datetime
from typing import Tuple

import pandas as pd
import streamlit as st

from pages_.common import (
    DEFAULT_STRING,
    DEFAULT_TENSION_LBS,
    STATUS_IN_PROGRESS,
    get_latest_job_for_customer,
    get_next_job_id,
    lbs_to_kg,
    safe_index,
    save_customers,
    save_jobs,
)


def page_new_job(
    jobs_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    strings_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    st.title("New Job")

    mode = st.radio("Customer", ["Existing", "New"], horizontal=True)

    latest_job = None

    if mode == "Existing" and not customers_df.empty:
        customer_name = st.selectbox(
            "Select customer", customers_df["customer_name"].tolist()
        )
        latest_job = get_latest_job_for_customer(jobs_df, customer_name)
    else:
        customer_name = st.text_input("Customer name")

    string_options = strings_df["string_type"].tolist()

    default_string = (
        latest_job["string_type"] if latest_job is not None else DEFAULT_STRING
    )
    default_tension = (
        int(latest_job["tension_lbs"])
        if latest_job is not None
        else DEFAULT_TENSION_LBS
    )

    with st.form("new_job_form"):
        string_type = st.selectbox(
            "String type",
            string_options,
            index=safe_index(string_options, default_string),
        )

        tension = st.slider("Tension (lbs)", 18, 34, default_tension, 1)

        with st.expander("Convert lbs to kg"):
            st.write(f"{tension} lbs ≈ {lbs_to_kg(tension)} kg")

        submitted = st.form_submit_button("Create Job")

    if submitted:
        if not customer_name.strip():
            st.error("Customer name required.")
            return jobs_df, customers_df

        if customer_name not in customers_df["customer_name"].values:
            customers_df.loc[len(customers_df)] = [customer_name]
            save_customers(customers_df)

        job_id = get_next_job_id(jobs_df)
        now = datetime.now().isoformat()

        new_row = {
            "job_id": job_id,
            "customer_name": customer_name,
            "string_type": string_type,
            "tension_lbs": tension,
            "status": STATUS_IN_PROGRESS,
            "created_at": now,
            "completed_at": "",
        }

        jobs_df = pd.concat([jobs_df, pd.DataFrame([new_row])], ignore_index=True)
        save_jobs(jobs_df)

        st.success(f"Job #{job_id} created.")

    return jobs_df, customers_df
