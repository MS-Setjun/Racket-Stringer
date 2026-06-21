from __future__ import annotations

import os
import zipfile
from typing import Tuple

import pandas as pd
import streamlit as st

from pages_.common import (
    ALLOWED_BACKUP_FILES,
    STATUS_COMPLETED_PAID,
    get_next_job_id,
    save_customers,
    save_jobs,
    save_strings,
)
from pages_.db import DB_PATH


def page_import_old_jobs(
    jobs_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    strings_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    st.title("Import / Backup Tools")

    st.write("Upload a CSV with columns: Customer_Name, String_Type, Tension.")
    st.write("Imported jobs are marked **Completed – Paid** with date **2024‑01‑01**.")

    import_mode = st.radio(
        "Import mode",
        ["Add to existing data", "Replace all data (fresh start)"],
        horizontal=True,
        help=(
            "Add to existing data: new rows are appended alongside your current "
            "jobs/customers/strings.\n\n"
            "Replace all data: deletes ALL existing jobs, customers, and string "
            "types first, then imports only what's in this CSV."
        ),
    )
    is_replace_mode = import_mode == "Replace all data (fresh start)"

    confirm_replace = False
    if is_replace_mode:
        st.warning(
            "⚠️ This will permanently delete all current jobs, customers, "
            "and string types before importing. Consider downloading a "
            "backup ZIP first (further down this page)."
        )
        confirm_replace = st.checkbox(
            "I understand this will erase all existing data."
        )

    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded is not None:
        try:
            df_old = pd.read_csv(uploaded)
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
            return jobs_df, customers_df, strings_df

        required_cols = {"Customer_Name", "String_Type", "Tension"}
        if not required_cols.issubset(df_old.columns):
            st.error("CSV must contain: Customer_Name, String_Type, Tension")
            return jobs_df, customers_df, strings_df

        import_disabled = is_replace_mode and not confirm_replace
        button_label = "Replace All Data" if is_replace_mode else "Import Jobs"

        if st.button(button_label, disabled=import_disabled):
            if is_replace_mode:
                jobs_df = jobs_df.iloc[0:0].copy()
                customers_df = customers_df.iloc[0:0].copy()
                strings_df = strings_df.iloc[0:0].copy()

            created_date = "2024-01-01T00:00:00"

            new_jobs = []
            skipped_rows = []

            for i, row in df_old.iterrows():
                customer = str(row["Customer_Name"]).strip()
                string_type = str(row["String_Type"]).strip()

                try:
                    tension = int(row["Tension"])
                except (ValueError, TypeError):
                    skipped_rows.append(i + 2)  # +2: header row + 1-indexing
                    continue

                if not customer or not string_type:
                    skipped_rows.append(i + 2)
                    continue

                if customer not in customers_df["customer_name"].values:
                    customers_df.loc[len(customers_df)] = [customer]

                if string_type not in strings_df["string_type"].values:
                    strings_df.loc[len(strings_df)] = [string_type]

                job_id = get_next_job_id(jobs_df)

                new_job = {
                    "job_id": job_id,
                    "customer_name": customer,
                    "string_type": string_type,
                    "tension_lbs": tension,
                    "status": STATUS_COMPLETED_PAID,
                    "created_at": created_date,
                    "completed_at": created_date,
                }

                jobs_df = pd.concat(
                    [jobs_df, pd.DataFrame([new_job])],
                    ignore_index=True
                )
                new_jobs.append(job_id)

            save_jobs(jobs_df)
            save_customers(customers_df)
            save_strings(strings_df)

            if new_jobs:
                verb = "Replaced data with" if is_replace_mode else "Imported"
                st.success(f"{verb} {len(new_jobs)} jobs successfully.")
            if skipped_rows:
                st.warning(
                    "Skipped rows with missing/invalid data "
                    f"(CSV line numbers): {', '.join(map(str, skipped_rows))}"
                )

            if is_replace_mode:
                st.rerun()

    st.markdown("---")
    st.subheader("Backup / Restore")

    # ---------------- BACKUP ----------------
    if st.button("Download Backup ZIP"):
        backup_path = "backup.zip"
        with zipfile.ZipFile(backup_path, "w") as z:
            if os.path.exists(DB_PATH):
                z.write(DB_PATH, arcname=os.path.basename(DB_PATH))

        with open(backup_path, "rb") as f:
            st.download_button(
                "Download backup.zip",
                f,
                file_name="backup.zip",
                mime="application/zip",
            )

    # ---------------- RESTORE ----------------
    uploaded_zip = st.file_uploader("Restore from ZIP", type=["zip"])

    if uploaded_zip is not None:
        try:
            with zipfile.ZipFile(uploaded_zip, "r") as z:
                names = z.namelist()

                # Reject anything that isn't exactly one of our known files.
                # This blocks zip-slip / path traversal and unexpected
                # payloads from a malicious or corrupted backup file.
                unexpected = [n for n in names if n not in ALLOWED_BACKUP_FILES]
                if unexpected:
                    st.error(
                        "Restore aborted — backup contains unexpected "
                        f"entries: {', '.join(unexpected)}"
                    )
                    return jobs_df, customers_df, strings_df

                if not names:
                    st.error("Restore aborted — backup ZIP is empty.")
                    return jobs_df, customers_df, strings_df

                app_dir = os.path.dirname(DB_PATH)
                for name in names:
                    z.extract(name, path=app_dir)

        except zipfile.BadZipFile:
            st.error("Restore aborted — not a valid ZIP file.")
            return jobs_df, customers_df, strings_df

        st.success("Backup restored successfully. Reloading...")
        st.rerun()

    return jobs_df, customers_df, strings_df