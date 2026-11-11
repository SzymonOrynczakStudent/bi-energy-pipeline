"""Main Dagster definitions entry point for the Canary Islands Energy BI pipeline."""

import shutil
from pathlib import Path
import dagster as dg
from dagster_dbt import DbtCliResource

from . import ingestion, reports
from .transformation import dbt_models, dbt_project

dbt_bin = shutil.which("dbt") or str(
    Path(__file__).parent.parent.parent / "venv" / "bin" / "dbt"
)

defs = dg.Definitions(
    assets=[
        *ingestion.raw_assets,
        dbt_models,
        reports.canary_energy_kpis_summary,
    ],
    executor=dg.in_process_executor,
    resources={
        "dbt": DbtCliResource(project_dir=dbt_project, dbt_executable=dbt_bin),
    },
)
