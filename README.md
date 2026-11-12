# ELT Pipeline: Canary Islands Energy Statistics (ISTAC C00022A)

Business Intelligence project built on the Modern Data Stack:
**Extract & Load (Python) $\longrightarrow$ Warehouse (PostgreSQL) $\longrightarrow$ Transform (dbt) $\longrightarrow$ Orchestration (Dagster)**.

---

## 1. Project Structure

```text
bi-energy-pipeline/
├── README.md                      # Step-by-step reproduction guide
├── requirements.txt               # Pinned Python dependencies
├── .env.example                   # Environment variable template (no secrets)
├── env.sh                         # Helper script activating venv and PG* variables
├── docker-compose.yml             # PostgreSQL service (postgres:16-alpine)
│
├── definition/
│   └── definition.yml             # SMART objectives, actors, research questions Q1-Q3 & KPIs
│
├── data/
│   └── raw_sources/
│       └── README.md              # ISTAC C00022A source metadata & license
│
├── ingestion/
│   ├── ingest_istac_raw.py        # Pure ELT ingestion from ISTAC REST API to 'raw' schema
│   └── verify_raw.py              # Verification script for 'raw' schema tables & counts
│
├── dbt/                           # dbt-core project (the T in ELT)
│   ├── dbt_project.yml            # Models, layers, and analytics_* schema configuration
│   ├── profiles.yml               # PostgreSQL profile reading environment variables
│   ├── seeds/                     # Reference CSV tables (canary_islands.csv, energy_technologies.csv)
│   ├── models/
│   │   ├── staging/               # Staging layer (clean views stg_*, _sources.yml, _staging.yml)
│   │   ├── intermediate/          # Intermediate layer (int_* views for KPIs and grid balance)
│   │   └── marts/                 # Marts layer (star schema: dim_*, fct_*, contracts & tests)
│   └── tests/                     # Singular business rule test for generation balance
│
├── orchestration/                 # Dagster orchestration project (assets & jobs)
│   ├── pyproject.toml
│   ├── workspace.yaml
│   └── energy_dagster/
│       ├── definitions.py
│       ├── ingestion.py
│       ├── transformation.py
│       └── reports.py
│
└── output/
    └── canary_energy_kpis_summary.csv  # Final exported KPI summary CSV
```

---

## 2. System Requirements & Tool Versions

* **OS**: Linux (Ubuntu 24.04 LTS or compatible)
* **Docker & Docker Compose**: Docker 29.x+, Compose v2.40+
* **Python**: 3.12+
* **Pinned Data Stack Versions**:
  * `dbt-core`: `1.12.5`
  * `dbt-postgres`: `1.11.0`
  * `dagster`: `1.13.26`
  * `dagster-dbt`: `0.29.26`
  * `psycopg2-binary`: `2.9.13`

---

## 3. Step-by-Step Reproduction Guide

### Step 1: Start PostgreSQL
From the project root:
```bash
docker compose up -d
docker compose ps
```

### Step 2: Set Up the Python Virtual Environment
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```
Load the environment helper in your terminal:
```bash
source env.sh
```

### Step 3: Run Raw Ingestion (Extract & Load to `raw` schema)
Downloads official ISTAC Operation `C00022A` CSV datasets and stores them verbatim in the PostgreSQL `raw` schema:
```bash
python ingestion/ingest_istac_raw.py
python ingestion/verify_raw.py
```

### Step 4: Build & Test Models with dbt
```bash
cd dbt
dbt debug
dbt build
```
*(Expected output: **48 of 48 nodes PASS**, covering 2 seeds, 10 models, 35 generic tests, and 1 singular balance test).*

To generate the catalog and data lineage documentation:
```bash
dbt docs generate
dbt docs serve --port 8080 --no-browser
```

### Step 5: Run Dagster Orchestration
```bash
cd ../orchestration
dg check defs
dg launch --assets reports/canary_energy_kpis_summary
```
To launch the Dagster Web UI locally on port `3000`:
```bash
dg dev -h 127.0.0.1 -p 3000
```

---

## 4. Control Figures (Verification Benchmarks)

1. **`raw` schema tables**:
   * `raw.c00022a_000001`: 19,200 rows
   * `raw.c00022a_000002`: 896 rows
   * `raw.c00022a_000004`: 47,400 rows
   * `raw.c00022a_000007`: 2,240 rows
   * `raw.c00022a_000008`: 49,920 rows

2. **`analytics_marts` schema tables**:
   * `dim_islands`: 8 rows (7 Canary Islands + archipelago total).
   * `dim_technologies`: 6 generation technologies.
   * `fct_monthly_generation`: 1,152 monthly island generation rows.
   * `fct_annual_sector_consumption`: 3,120 annual sector consumption rows.

3. **Key Analytical Findings**:
   * **Renewable Penetration in El Hierro**: Grew from **0.71% in 2010** to **47.17% in 2021** (driven by the Gorona del Viento hydro-wind plant).
   * **Canary Islands Total Renewable Share**: Grew from **6.00% in 2010** to **19.94% in 2021**.
   * **Largest Electricity Consumer Sector**: Households (*Hogares*), exceeding 5.8M MWh and 2M CUPS connections.
