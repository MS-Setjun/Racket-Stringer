from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(APP_DIR / "stringing.db")

# Legacy CSV locations — only used for one-time migration into SQLite.
_LEGACY_JOBS_CSV = str(APP_DIR / "jobs.csv")
_LEGACY_CUSTOMERS_CSV = str(APP_DIR / "customers.csv")
_LEGACY_STRINGS_CSV = str(APP_DIR / "strings.csv")

DEFAULT_STRING = "Yonex BG80"

JOBS_COLUMNS = [
    "job_id",
    "customer_name",
    "string_type",
    "tension_lbs",
    "status",
    "created_at",
    "completed_at",
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS strings (
            string_type TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS customers (
            customer_name TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS jobs (
            job_id        INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            string_type   TEXT NOT NULL,
            tension_lbs   INTEGER NOT NULL,
            status        TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            completed_at  TEXT
        );
        """
    )
    conn.commit()


def _migrate_legacy_csvs(conn: sqlite3.Connection) -> None:
    """One-time import of pre-existing jobs/customers/strings CSVs into the
    new SQLite database, so upgrading doesn't lose historical data."""

    if os.path.exists(_LEGACY_STRINGS_CSV):
        df = pd.read_csv(_LEGACY_STRINGS_CSV, dtype={"string_type": "string"})
        conn.executemany(
            "INSERT OR IGNORE INTO strings (string_type) VALUES (?)",
            [(str(v),) for v in df["string_type"].dropna()],
        )

    if os.path.exists(_LEGACY_CUSTOMERS_CSV):
        df = pd.read_csv(_LEGACY_CUSTOMERS_CSV, dtype={"customer_name": "string"})
        conn.executemany(
            "INSERT OR IGNORE INTO customers (customer_name) VALUES (?)",
            [(str(v),) for v in df["customer_name"].dropna()],
        )

    if os.path.exists(_LEGACY_JOBS_CSV):
        df = pd.read_csv(
            _LEGACY_JOBS_CSV,
            dtype={
                "job_id": "Int64",
                "customer_name": "string",
                "string_type": "string",
                "tension_lbs": "Int64",
                "status": "string",
                "created_at": "string",
                "completed_at": "string",
            },
        )
        records = []
        for row in df.itertuples(index=False):
            records.append(
                (
                    int(row.job_id),
                    str(row.customer_name),
                    str(row.string_type),
                    int(row.tension_lbs),
                    str(row.status),
                    str(row.created_at),
                    None if pd.isna(row.completed_at) else str(row.completed_at),
                )
            )
        conn.executemany(
            f"INSERT OR IGNORE INTO jobs ({', '.join(JOBS_COLUMNS)}) "
            f"VALUES ({', '.join('?' for _ in JOBS_COLUMNS)})",
            records,
        )

    conn.commit()


def init_db() -> None:
    """Create the database/schema if needed, seed defaults, and migrate any
    legacy CSV data the very first time the database is created."""
    is_new_db = not os.path.exists(DB_PATH)

    conn = get_connection()
    try:
        _create_schema(conn)

        if is_new_db:
            _migrate_legacy_csvs(conn)

        cur = conn.execute("SELECT COUNT(*) FROM strings")
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT OR IGNORE INTO strings (string_type) VALUES (?)",
                (DEFAULT_STRING,),
            )
            conn.commit()
    finally:
        conn.close()
