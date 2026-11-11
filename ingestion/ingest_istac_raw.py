#!/usr/bin/env python3
"""
Raw Ingestion Script for Canary Islands Energy Statistics (ISTAC Operation C00022A).

Modern Data Stack - ELT Extract & Load:
Fetches raw CSV payloads from the ISTAC Open Data REST API and loads them
verbatim into the PostgreSQL 'raw' schema without transformations or column renaming.
Adds only the '_loaded_at' UTC ingestion control timestamp.
"""

import argparse
from datetime import datetime, timezone
import io
import logging
import os
import sys

import pandas as pd
import requests
from sqlalchemy import create_engine, inspect, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("istac_ingest")

# Core ISTAC Operation C00022A datasets:
# - C00022A_000001: Final consumption & clients by sector (2010-2019)
# - C00022A_000002: Final consumption & clients by sector (2020+)
# - C00022A_000004: Gross production, internal demand & final consumption
# - C00022A_000007: Net electricity generation by source & grid system
# - C00022A_000008: Net electricity generation by source & island
DEFAULT_DATASETS = [
    "C00022A_000001",
    "C00022A_000002",
    "C00022A_000004",
    "C00022A_000007",
    "C00022A_000008",
]

BASE_API_URL = "https://datos.canarias.es/api/estadisticas/statistical-resources/v1.0/datasets/ISTAC"


def get_db_engine():
    """Build SQLAlchemy engine from environment variables."""
    user = os.getenv("POSTGRES_USER", "raw_user")
    password = os.getenv("POSTGRES_PASSWORD", "raw_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "raw_db")

    uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(uri)


def resolve_download_url(dataset_id: str) -> str:
    """Resolve the latest version resource URL for a given ISTAC dataset ID."""
    meta_url = f"{BASE_API_URL}/{dataset_id}"
    resp = requests.get(meta_url, headers={"Accept": "application/json"}, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("dataset", [])
    if not items:
        raise ValueError(f"Dataset {dataset_id} not found in ISTAC metadata.")
    return items[0]["selfLink"]["href"]


def fetch_raw_dataset(dataset_id: str) -> pd.DataFrame:
    """Download CSV data in raw string format while preserving UTF-8 encoding."""
    download_url = resolve_download_url(dataset_id)
    logger.info("Fetching CSV for %s from %s", dataset_id, download_url)

    resp = requests.get(download_url, headers={"Accept": "text/csv"}, timeout=60)
    resp.raise_for_status()

    # Decode explicitly as UTF-8 to preserve Spanish accents in raw source values
    csv_text = resp.content.decode("utf-8")
    df = pd.read_csv(io.StringIO(csv_text), dtype=str, keep_default_na=False)

    # Add ingestion control column
    df["_loaded_at"] = datetime.now(timezone.utc).isoformat()
    return df


def ingest_to_raw_schema(df: pd.DataFrame, table_name: str, engine):
    """Load raw DataFrame into PostgreSQL 'raw' schema without breaking dependent views."""
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        table_exists = inspect(conn).has_table(table_name, schema="raw")

        if table_exists:
            existing_cols = [c["name"] for c in inspect(conn).get_columns(table_name, schema="raw")]
            if existing_cols == list(df.columns):
                logger.info("Truncating raw.%s and appending %d rows...", table_name, len(df))
                conn.execute(text(f'TRUNCATE TABLE raw."{table_name}";'))
                df.to_sql(
                    name=table_name,
                    schema="raw",
                    con=conn,
                    if_exists="append",
                    index=False,
                    chunksize=5000,
                    method="multi",
                )
            else:
                logger.info("Schema changed for raw.%s; recreating with CASCADE...", table_name)
                conn.execute(text(f'DROP TABLE raw."{table_name}" CASCADE;'))
                df.to_sql(
                    name=table_name,
                    schema="raw",
                    con=conn,
                    if_exists="replace",
                    index=False,
                    chunksize=5000,
                    method="multi",
                )
        else:
            logger.info("Creating raw.%s with %d rows...", table_name, len(df))
            df.to_sql(
                name=table_name,
                schema="raw",
                con=conn,
                if_exists="replace",
                index=False,
                chunksize=5000,
                method="multi",
            )
    logger.info("Table raw.%s loaded successfully.", table_name)


def main():
    parser = argparse.ArgumentParser(description="Ingest ISTAC C00022A datasets into raw schema.")
    parser.add_argument("--datasets", nargs="+", default=DEFAULT_DATASETS)
    args = parser.parse_args()

    engine = get_db_engine()

    for dataset_id in args.datasets:
        table_name = dataset_id.lower()
        try:
            df = fetch_raw_dataset(dataset_id)
            ingest_to_raw_schema(df, table_name, engine)
        except Exception as exc:
            logger.error("Failed to ingest %s: %s", dataset_id, exc)

    logger.info("Ingestion to schema 'raw' completed.")


if __name__ == "__main__":
    main()

