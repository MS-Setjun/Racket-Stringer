from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from pages_.common import LOGO_PATH, save_strings


def sidebar_navigation() -> str:
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(image=LOGO_PATH, use_container_width=True)
    st.sidebar.title("Navigation")
    return st.sidebar.radio(
        "",
        (
            "🏠 Dashboard",
            "➕ New Job",
            "📦 Finished & Paid Jobs",
            "👤 Customers",
            "📊 Analytics Dashboard",
            "📥 Import / Backup",
        ),
    )


def sidebar_string_catalogue(
    strings_df: pd.DataFrame, jobs_df: pd.DataFrame
) -> pd.DataFrame:
    with st.sidebar.expander("String Catalogue", expanded=False):

        st.write("Manage available string types.")

        # Add new string
        with st.form("add_string_form", clear_on_submit=True):
            new_string = st.text_input("New string type")
            if st.form_submit_button("Add") and new_string.strip():
                if new_string not in strings_df["string_type"].values:
                    strings_df.loc[len(strings_df)] = [new_string.strip()]
                    save_strings(strings_df)
                    st.success("Added.")
                else:
                    st.warning("Already exists.")

        # Delete strings
        delete_choice = st.multiselect(
            "Delete strings",
            strings_df["string_type"].tolist()
        )
        if st.button("Delete selected"):
            in_use = set(jobs_df["string_type"].dropna().unique())
            blocked = [s for s in delete_choice if s in in_use]
            removable = [s for s in delete_choice if s not in in_use]

            if removable:
                strings_df = strings_df[
                    ~strings_df["string_type"].isin(removable)
                ].reset_index(drop=True)
                save_strings(strings_df)
                st.success(f"Deleted: {', '.join(removable)}")

            if blocked:
                st.warning(
                    "Skipped (still used by existing jobs): "
                    f"{', '.join(blocked)}"
                )

    return strings_df
