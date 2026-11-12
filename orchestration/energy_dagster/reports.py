"""Final reporting and KPI export assets built from analytics_marts."""

import os
from pathlib import Path
import dagster as dg
from dagster_dbt import get_asset_key_for_model
import pandas as pd
from sqlalchemy import create_engine

from .transformation import dbt_models

OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"


@dg.asset(
    key=["reports", "canary_energy_kpis_summary"],
    group_name="reports",
    kinds={"python", "csv"},
    deps=[get_asset_key_for_model([dbt_models], "fct_monthly_generation")],
    description="Exports annual renewable energy share and total generation KPIs per island to a CSV report.",
)
def canary_energy_kpis_summary(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    user = os.getenv("POSTGRES_USER", "raw_user")
    password = os.getenv("POSTGRES_PASSWORD", "raw_password")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("DW_POSTGRES_DB", "analytics_db")

    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")

    query = """
    SELECT 
        island_name,
        year,
        ROUND(AVG(renewable_share_pct), 2) AS avg_renewable_share_pct,
        ROUND(SUM(renewable_generation_mwh), 0) AS total_renewable_mwh,
        ROUND(SUM(total_generation_mwh), 0) AS total_generation_mwh
    FROM analytics_marts.fct_monthly_generation
    GROUP BY island_name, year
    ORDER BY island_name, year;
    """

    df = pd.read_sql(query, con=engine)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "canary_energy_kpis_summary.csv"
    df.to_csv(output_file, index=False)

    context.log.info(f"Report generated with {len(df)} rows at {output_file}")
    return dg.MaterializeResult(
        metadata={
            "row_count": len(df),
            "output_path": str(output_file),
        }
    )

