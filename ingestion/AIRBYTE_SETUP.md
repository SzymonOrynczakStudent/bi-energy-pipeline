# Airbyte Configuration Guide (`raw_db` $\rightarrow$ `analytics_db`)

This document describes the step-by-step configuration of **Airbyte Community (`v2.5.0`)** deployed on the VM (`http://localhost:8000`) to replicate raw ISTAC energy tables from **PostgreSQL Source (`raw_db`)** into **PostgreSQL Destination (`analytics_db`)**.

---

## 1. Architecture Role

1. **Extract & Load to Source DB**: [`ingest_istac_raw.py`](./ingest_istac_raw.py) fetches raw CSV payloads from the ISTAC REST API (`C00022A`) and loads them into `raw_db` (schema `raw`).
2. **Database-to-Database Replication (Airbyte)**: Airbyte replicates the 5 tables from `raw_db.raw` to `analytics_db.raw`, appending Airbyte control metadata (`_airbyte_raw_id`, `_airbyte_extracted_at`, `_airbyte_meta`, `_airbyte_generation_id`).
3. **Transformation (dbt)** & **Orchestration (Dagster)**: dbt transforms `analytics_db.raw` into `analytics_staging`, `analytics_intermediate`, and `analytics_marts`.

---

## 2. Step-by-Step UI Configuration

### Step 1: Source Setup (`Postgres Raw DB`)
In the Airbyte UI (**Sources** $\rightarrow$ **+ New source** $\rightarrow$ **Postgres**):

| Parameter | Value |
| :--- | :--- |
| **Source name** | `Postgres Raw DB` |
| **Host** | `172.19.0.1` *(Docker bridge IP to reach host Postgres from Airbyte container)* |
| **Port** | `5432` |
| **DB Name** | `raw_db` |
| **User** | `raw_user` |
| **Password** | `<POSTGRES_PASSWORD>` |
| **Schemas** | `raw` |
| **SSL Mode** | `disable` |
| **Update Method** | `Scan Changes with User Defined Cursor` |

---

### Step 2: Destination Setup (`Postgres Analytics DB`)
In the Airbyte UI (**Destinations** $\rightarrow$ **+ New destination** $\rightarrow$ **Postgres**):

| Parameter | Value |
| :--- | :--- |
| **Destination name** | `Postgres Analytics DB` |
| **Host** | `172.19.0.1` |
| **Port** | `5432` |
| **DB Name** | `analytics_db` |
| **User** | `raw_user` |
| **Password** | `<POSTGRES_PASSWORD>` |
| **Default Schema** | `raw` |
| **SSL Mode** | `disable` |

---

### Step 3: Connection & Stream Selection
In **Connections** $\rightarrow$ **+ New connection** (`Postgres Raw DB` $\rightarrow$ `Postgres Analytics DB`):

* **Selected Streams (5 tables from `raw`):**
  * `c00022a_000001`
  * `c00022a_000002`
  * `c00022a_000004`
  * `c00022a_000007`
  * `c00022a_000008`
* **Sync Mode**: **`Full refresh | Overwrite`** for all 5 streams.
  * *Why*: Raw ISTAC tables do not define a composite primary key in `raw_db`, and `Full refresh | Overwrite` guarantees an idempotent, duplicate-free snapshot on every sync.

---

### Step 4: Configure Connection & Run Sync
* **Schedule type**: `Manual`
* **Destination Namespace**: `Destination default` (`raw`)
* **Execution**: Click **Finish & Sync** (or **Sync now** on the connection page) and verify the job completes with status **Succeeded**.

