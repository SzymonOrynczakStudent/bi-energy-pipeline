#!/usr/bin/env python3
"""
Verification Script for PostgreSQL 'raw' schema.
Queries the database to inspect raw tables, column counts, and record totals.
"""

import os
from sqlalchemy import create_engine, inspect, text


def verify_raw():
    user = os.getenv("POSTGRES_USER", "raw_user")
    password = os.getenv("POSTGRES_PASSWORD", "raw_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "raw_db")

    uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    engine = create_engine(uri)

    print("=" * 70)
    print(f"Connecting to {host}:{port}/{db} (Schema: raw)...")
    with engine.connect() as conn:
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema="raw")
        print(f"Total Tables in 'raw' schema: {len(tables)}")
        print("=" * 70)

        for table in sorted(tables):
            cols = inspector.get_columns(table, schema="raw")
            count = conn.execute(text(f'SELECT COUNT(*) FROM raw."{table}"')).scalar()
            print(f"Table: raw.{table:25} | Columns: {len(cols):2} | Records: {count:8,}")

        print("=" * 70)


if __name__ == "__main__":
    verify_raw()

