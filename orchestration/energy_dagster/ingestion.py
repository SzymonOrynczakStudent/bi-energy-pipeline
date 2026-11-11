"""Extract and Load (EL) assets fetching ISTAC datasets into the PostgreSQL raw schema."""

from pathlib import Path
import sys

import dagster as dg

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.ingest_istac_raw import (  # noqa: E402
    fetch_raw_dataset,
    get_db_engine,
    ingest_to_raw_schema,
)

ISTAC_DATASETS = {
    "C00022A_000001": "Final electricity consumption and customers by sector (2010-2019).",
    "C00022A_000002": "Final electricity consumption and customers by sector (2020-present).",
    "C00022A_000004": "Monthly electrical balance: gross production, demand, and final consumption.",
    "C00022A_000007": "Net electricity generation by energy source and electrical system.",
    "C00022A_000008": "Net electricity generation by energy source per island.",
}


def build_raw_asset(dataset_id: str, description: str) -> dg.AssetsDefinition:
    """Create a Dagster asset that extracts and loads a single ISTAC dataset into raw."""
    table_name = dataset_id.lower()

    @dg.asset(
        key=["raw", table_name],
        group_name="ingestion",
        kinds={"python", "postgres"},
        description=description,
    )
    def _raw_asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
        context.log.info(f"Fetching ISTAC dataset {dataset_id}...")
        df = fetch_raw_dataset(dataset_id)
        engine = get_db_engine()
        ingest_to_raw_schema(df, table_name, engine)
        context.log.info(f"Loaded {len(df)} rows into raw.{table_name}.")
        return dg.MaterializeResult(
            metadata={
                "dagster/row_count": len(df),
                "dataset_id": dataset_id,
                "target_table": f"raw.{table_name}",
            }
        )

    return _raw_asset


raw_assets = [
    build_raw_asset(dataset_id, description)
    for dataset_id, description in ISTAC_DATASETS.items()
]
