from __future__ import annotations

from typing import Tuple

import pandas as pd
import streamlit as st

from pages_.common import save_customers, save_jobs


def page_customers(
    customers_df: pd.DataFrame, jobs_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    st.title("Customers")

    name_filter = st.text_input("Search")

    filtered = customers_df.copy()
    if name_filter:
        filtered = filtered[
            filtered["customer_name"].str.contains(name_filter, case=False)
        ]

    st.dataframe(filtered, width="stretch")

    for _, row in filtered.iterrows():
        with st.expander(row["customer_name"]):
            new_name = st.text_input(
                "New name",
                value=row["customer_name"],
                key=f"cust_{row['customer_name']}",
            )

            if st.button("Save", key=f"cust_save_{row['customer_name']}"):
                new_name = new_name.strip()

                if not new_name:
                    st.error("Name cannot be empty.")
                elif (
                    new_name != row["customer_name"]
                    and new_name in customers_df["customer_name"].values
                ):
                    st.error(f"A customer named '{new_name}' already exists.")
                else:
                    customers_df.loc[
                        customers_df["customer_name"] == row["customer_name"],
                        "customer_name",
                    ] = new_name

                    jobs_df.loc[
                        jobs_df["customer_name"] == row["customer_name"],
                        "customer_name",
                    ] = new_name

                    save_customers(customers_df)
                    save_jobs(jobs_df)

                    st.success("Updated.")
                    st.rerun()

    return customers_df, jobs_df
