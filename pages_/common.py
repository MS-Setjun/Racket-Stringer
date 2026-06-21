from __future__ import annotations

import html
import os

import pandas as pd

from pages_.db import DB_PATH, JOBS_COLUMNS, get_connection, init_db

# ---------------------------------------------------------------------
# Configuration & constants
# ---------------------------------------------------------------------

APP_DIR = os.path.dirname(DB_PATH)

LOGO_PATH = os.path.join(APP_DIR, "logo.png")
FAVICON_PATH = os.path.join(APP_DIR, "favicon.png")

STATUS_IN_PROGRESS = "In Progress"
STATUS_COMPLETED_UNPAID = "Completed – Unpaid"
STATUS_COMPLETED_PAID = "Completed – Paid"
STATUS_CANCELLED = "Cancelled"

JOB_STATUSES = [
    STATUS_IN_PROGRESS,
    STATUS_COMPLETED_UNPAID,
    STATUS_COMPLETED_PAID,
    STATUS_CANCELLED,
]

DEFAULT_STRING = "Yonex BG80"
DEFAULT_TENSION_LBS = 26

# Used by the backup/restore page — only the DB file is included now.
ALLOWED_BACKUP_FILES = {os.path.basename(DB_PATH)}

# ---------------------------------------------------------------------
# Data loading / saving helpers (SQLite-backed)
# ---------------------------------------------------------------------

def load_or_init_jobs() -> pd.DataFrame:
    """Load all jobs from the database as a DataFrame with consistent dtypes."""
    init_db()
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            f"SELECT {', '.join(JOBS_COLUMNS)} FROM jobs ORDER BY job_id", conn
        )
    finally:
        conn.close()

    if df.empty:
        df = pd.DataFrame({col: pd.Series(dtype="object") for col in JOBS_COLUMNS})

    df["job_id"] = df["job_id"].astype("Int64")
    df["tension_lbs"] = df["tension_lbs"].astype("Int64")
    for col in ("customer_name", "string_type", "status", "created_at", "completed_at"):
        df[col] = df[col].astype("string")

    return df


def load_or_init_customers() -> pd.DataFrame:
    init_db()
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT customer_name FROM customers ORDER BY customer_name", conn
        )
    finally:
        conn.close()

    if df.empty:
        df = pd.DataFrame({"customer_name": pd.Series(dtype="object")})
    df["customer_name"] = df["customer_name"].astype("string")
    return df


def load_or_init_strings() -> pd.DataFrame:
    init_db()
    conn = get_connection()
    try:
        df = pd.read_sql_query(
            "SELECT string_type FROM strings ORDER BY string_type", conn
        )
    finally:
        conn.close()

    if df.empty:
        df = pd.DataFrame({"string_type": pd.Series(dtype="object")})
    df["string_type"] = df["string_type"].astype("string")
    return df


def save_jobs(df: pd.DataFrame) -> None:
    """Persist the full jobs table (replace-all semantics, matching the
    previous CSV behaviour) inside a single transaction."""
    records = []
    for row in df[JOBS_COLUMNS].itertuples(index=False):
        job_id, customer_name, string_type, tension_lbs, status, created_at, completed_at = row
        records.append(
            (
                int(job_id),
                str(customer_name),
                str(string_type),
                int(tension_lbs),
                str(status),
                str(created_at),
                None if pd.isna(completed_at) or completed_at == "" else str(completed_at),
            )
        )

    conn = get_connection()
    try:
        conn.execute("DELETE FROM jobs")
        conn.executemany(
            f"INSERT INTO jobs ({', '.join(JOBS_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in JOBS_COLUMNS)})",
            records,
        )
        conn.commit()
    finally:
        conn.close()


def save_customers(df: pd.DataFrame) -> None:
    names = [str(v) for v in df["customer_name"].dropna().unique()]
    conn = get_connection()
    try:
        conn.execute("DELETE FROM customers")
        conn.executemany(
            "INSERT OR IGNORE INTO customers (customer_name) VALUES (?)",
            [(n,) for n in names],
        )
        conn.commit()
    finally:
        conn.close()


def save_strings(df: pd.DataFrame) -> None:
    types_ = [str(v) for v in df["string_type"].dropna().unique()]
    conn = get_connection()
    try:
        conn.execute("DELETE FROM strings")
        conn.executemany(
            "INSERT OR IGNORE INTO strings (string_type) VALUES (?)",
            [(t,) for t in types_],
        )
        conn.commit()
    finally:
        conn.close()


def get_next_job_id(jobs_df: pd.DataFrame) -> int:
    if jobs_df.empty:
        return 1
    return int(jobs_df["job_id"].max()) + 1


def get_latest_job_for_customer(
    jobs_df: pd.DataFrame, customer_name: str
) -> pd.Series | None:
    customer_jobs = jobs_df[jobs_df["customer_name"] == customer_name]
    if customer_jobs.empty:
        return None
    customer_jobs = customer_jobs.sort_values("created_at", ascending=False)
    return customer_jobs.iloc[0]


def safe_index(options: list, value, default: int = 0) -> int:
    """Return options.index(value), or `default` if value isn't present.

    Prevents crashes when a job references a string type (or status) that
    has since been removed/renamed elsewhere in the app.
    """
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return default


def esc(value) -> str:
    """HTML-escape a value before interpolating it into unsafe_allow_html
    markup, to prevent stored XSS via customer names / string types."""
    return html.escape(str(value))


def lbs_to_kg(lbs: float) -> float:
    return round(lbs * 0.45359237, 2)
