from __future__ import annotations

import os

import streamlit as st

from pages_.analytics import page_analytics
from pages_.common import (
    FAVICON_PATH,
    load_or_init_customers,
    load_or_init_jobs,
    load_or_init_strings,
    save_customers,
    save_jobs,
    save_strings,
)
from pages_.customers import page_customers
from pages_.dashboard import page_dashboard
from pages_.finished_paid import page_finished_paid
from pages_.import_backup import page_import_old_jobs
from pages_.new_job import page_new_job
from pages_.sidebar import sidebar_navigation, sidebar_string_catalogue


def main() -> None:
    """Entry point for the Streamlit app."""

    page_icon = FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🏸"
    st.set_page_config(page_title="Racket Stringing", layout="wide", page_icon=page_icon)

    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
                max-width: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    jobs_df = load_or_init_jobs()
    customers_df = load_or_init_customers()
    strings_df = load_or_init_strings()

    page = sidebar_navigation()
    strings_df = sidebar_string_catalogue(strings_df, jobs_df)

    match page:
        case "🏠 Dashboard":
            jobs_df = page_dashboard(jobs_df, strings_df)

        case "➕ New Job":
            jobs_df, customers_df = page_new_job(
                jobs_df, customers_df, strings_df
            )

        case "📦 Finished & Paid Jobs":
            jobs_df = page_finished_paid(jobs_df)

        case "👤 Customers":
            customers_df, jobs_df = page_customers(
                customers_df, jobs_df
            )

        case "📥 Import / Backup":
            jobs_df, customers_df, strings_df = page_import_old_jobs(
                jobs_df, customers_df, strings_df
            )

        case "📊 Analytics Dashboard":
            page_analytics(jobs_df)

        case _:
            st.error("Unknown page selected.")

    save_jobs(jobs_df)
    save_customers(customers_df)
    save_strings(strings_df)


if __name__ == "__main__":
    main()
