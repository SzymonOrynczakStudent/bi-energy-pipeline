"""Canary Islands Electrical Energy BI Dashboard.

Interactive Business Intelligence application presenting the analytical marts
produced by dbt Core and orchestrated by Dagster for ISTAC Operation C00022A.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

# --- Page Configuration ---
st.set_page_config(
    page_title="Canary Islands Energy BI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for executive look
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #2563EB;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Database Connection ---
@st.cache_resource
def get_db_engine():
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    database = os.getenv("PGDATABASE", "analytics_db")
    user = os.getenv("PGUSER", "raw_user")
    password = os.getenv("PGPASSWORD", "raw_password")
    conn_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    return create_engine(conn_str)


# --- Data Loaders (Cached) ---
@st.cache_data(ttl=600)
def load_dim_islands():
    engine = get_db_engine()
    return pd.read_sql("SELECT * FROM analytics_marts.dim_islands ORDER BY island_name", engine)


@st.cache_data(ttl=600)
def load_monthly_generation():
    engine = get_db_engine()
    sql = """
    SELECT 
        period_code,
        year,
        month,
        date,
        territory_code,
        island_name,
        province,
        grid_system,
        renewable_generation_mwh,
        fossil_generation_mwh,
        total_generation_mwh,
        renewable_share_pct
    FROM analytics_marts.fct_monthly_generation
    ORDER BY date, island_name
    """
    return pd.read_sql(sql, engine)


@st.cache_data(ttl=600)
def load_technology_generation():
    engine = get_db_engine()
    sql = """
    SELECT 
        stg.period_code,
        stg.year,
        stg.month,
        stg.territory_name AS island_name,
        COALESCE(dim.technology_name, stg.source_technology_name) AS technology_name,
        dim.category,
        COALESCE(dim.is_renewable, stg.is_renewable) AS is_renewable,
        stg.generation_mwh
    FROM analytics_staging.stg_electricity_generation stg
    LEFT JOIN analytics_marts.dim_technologies dim
        ON stg.technology_code = dim.technology_code
    ORDER BY stg.year, stg.month
    """
    return pd.read_sql(sql, engine)


@st.cache_data(ttl=600)
def load_sector_consumption():
    engine = get_db_engine()
    sql = """
    SELECT 
        sector_consumption_id,
        year,
        territory_code,
        island_name,
        sector_code,
        sector_name,
        consumption_mwh,
        customer_cups_count
    FROM analytics_marts.fct_annual_sector_consumption
    ORDER BY year, island_name, sector_name
    """
    return pd.read_sql(sql, engine)


@st.cache_data(ttl=600)
def load_balance_efficiency():
    engine = get_db_engine()
    sql = """
    SELECT 
        balance_id,
        period_code,
        year,
        month,
        date,
        territory_code,
        island_name,
        gross_production_mwh,
        internal_demand_mwh,
        final_consumption_mwh,
        transmission_distribution_losses_mwh,
        grid_loss_rate_pct
    FROM analytics_marts.fct_balance_efficiency
    ORDER BY date, island_name
    """
    return pd.read_sql(sql, engine)


# --- Load Data ---
try:
    df_islands = load_dim_islands()
    df_gen = load_monthly_generation()
    df_tech = load_technology_generation()
    df_cons = load_sector_consumption()
    df_bal = load_balance_efficiency()
    db_connected = True
except Exception as e:
    st.error(f"Error connecting to PostgreSQL analytics_db: {e}")
    st.info("Make sure PostgreSQL is running: `docker compose up -d` and `source env.sh`.")
    st.stop()


# --- Sidebar Filters ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/b/b0/Flag_of_the_Canary_Islands.svg", width=90)
st.sidebar.title("Canary Islands BI")
st.sidebar.markdown("**ISTAC Operation C00022A**  \n*Electrical Energy Statistics*")
st.sidebar.divider()

# Island Selection
island_list = ["All Islands (Archipelago)"] + sorted(list(df_islands["island_name"].unique()))
selected_island = st.sidebar.selectbox("Select Territory / Island:", island_list, index=0)

# Year Range Selection
min_year = int(df_gen["year"].min())
max_year = int(df_gen["year"].max())
selected_years = st.sidebar.slider(
    "Select Year Range:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

st.sidebar.divider()
st.sidebar.markdown(
    """
    **Data Stack Architecture:**
    - 📥 **Ingestion**: Python REST API client
    - 🔄 **Replication**: Airbyte ELT
    - 🏛️ **Warehouse**: PostgreSQL 16
    - ⚡ **Transforms**: dbt Core (48 tests pass)
    - 🎯 **Orchestrator**: Dagster 1.13
    - 📊 **BI App**: Streamlit + Plotly
    """
)
st.sidebar.caption("© 2026 Szymon Oryńczak | ULL BI Project")


# --- Filter Data by Selection ---
year_start, year_end = selected_years

# Filter generation
df_gen_filtered = df_gen[(df_gen["year"] >= year_start) & (df_gen["year"] <= year_end)]
df_tech_filtered = df_tech[(df_tech["year"] >= year_start) & (df_tech["year"] <= year_end)]
df_cons_filtered = df_cons[(df_cons["year"] >= year_start) & (df_cons["year"] <= year_end)]
df_bal_filtered = df_bal[(df_bal["year"] >= year_start) & (df_bal["year"] <= year_end)]

if selected_island != "All Islands (Archipelago)":
    df_gen_filtered = df_gen_filtered[df_gen_filtered["island_name"] == selected_island]
    df_tech_filtered = df_tech_filtered[df_tech_filtered["island_name"] == selected_island]
    df_cons_filtered = df_cons_filtered[df_cons_filtered["island_name"] == selected_island]
    df_bal_filtered = df_bal_filtered[df_bal_filtered["island_name"] == selected_island]


# --- Header Section ---
st.markdown('<div class="main-header">⚡ Canary Islands Electrical Energy BI Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-header">Executive Monitoring & Strategic Decision Support | Scope: <b>{selected_island}</b> ({year_start} – {year_end})</div>',
    unsafe_allow_html=True,
)


# --- KPI Cards Row ---
col1, col2, col3, col4, col5 = st.columns(5)

total_net_gen = df_gen_filtered["total_generation_mwh"].sum()
total_renew_gen = df_gen_filtered["renewable_generation_mwh"].sum()
overall_renew_share = (total_renew_gen / total_net_gen * 100) if total_net_gen > 0 else 0
total_consumption = df_cons_filtered["consumption_mwh"].sum()
avg_loss_rate = df_bal_filtered["grid_loss_rate_pct"].mean()

with col1:
    st.metric(
        label="Net Generation",
        value=f"{total_net_gen / 1e6:.2f} TWh" if total_net_gen >= 1e6 else f"{total_net_gen:,.0f} MWh",
        help="Total net electricity generated and injected into the grid.",
    )

with col2:
    st.metric(
        label="Renewable Generation",
        value=f"{total_renew_gen / 1e6:.2f} TWh" if total_renew_gen >= 1e6 else f"{total_renew_gen:,.0f} MWh",
        help="Electricity generated by Wind, Solar PV, Hydro and Biogas.",
    )

with col3:
    st.metric(
        label="Renewable Share (%)",
        value=f"{overall_renew_share:.1f}%",
        delta=f"{overall_renew_share - 30.0:.1f}% vs 30% Target",
        delta_color="normal" if overall_renew_share >= 30.0 else "inverse",
        help="Strategic Objective O1: Exceed 30% renewable generation.",
    )

with col4:
    st.metric(
        label="Final Consumption",
        value=f"{total_consumption / 1e6:.2f} TWh" if total_consumption >= 1e6 else f"{total_consumption:,.0f} MWh",
        help="Total electrical energy consumed by end-use economic sectors.",
    )

with col5:
    loss_delta = 8.0 - avg_loss_rate
    st.metric(
        label="Avg Grid Loss Rate",
        value=f"{avg_loss_rate:.2f}%",
        delta=f"{loss_delta:+.2f}% vs 8% Target",
        delta_color="normal" if avg_loss_rate <= 8.0 else "inverse",
        help="Strategic Objective O2: Maintain grid losses below 8%.",
    )

st.markdown("<br>", unsafe_allow_html=True)


# --- Tabs for Research Questions ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🌿 Q1: Renewable Transition (Mix & Evolution)",
    "🏢 Q2: Sectoral Electricity Consumption",
    "🔌 Q3: Grid Efficiency & Losses",
    "🏛️ Data Architecture & Lineage",
])


# ==============================================================================
# TAB 1: Renewable Transition (Q1)
# ==============================================================================
with tab1:
    st.subheader("Research Question 1: Evolution of the Renewable Energy Mix")
    st.caption("Addressing Actor: Director General of Ecological Transition (Strategic Decision Support)")

    # Annual Aggregation for Share
    annual_gen = (
        df_gen_filtered.groupby("year")[["renewable_generation_mwh", "fossil_generation_mwh", "total_generation_mwh"]]
        .sum()
        .reset_index()
    )
    annual_gen["renewable_share_pct"] = (
        annual_gen["renewable_generation_mwh"] / annual_gen["total_generation_mwh"] * 100
    ).round(2)

    col_t1, col_t2 = st.columns([1, 1])

    with col_t1:
        fig_share = go.Figure()
        fig_share.add_trace(
            go.Scatter(
                x=annual_gen["year"],
                y=annual_gen["renewable_share_pct"],
                mode="lines+markers",
                name="Renewable Share (%)",
                line=dict(color="#10B981", width=3),
                marker=dict(size=8),
            )
        )
        # Target Line 30%
        fig_share.add_hline(
            y=30.0,
            line_dash="dash",
            line_color="#EF4444",
            annotation_text="Strategic Target (30%)",
            annotation_position="bottom right",
        )
        fig_share.update_layout(
            title="Annual Renewable Share (%) Trend",
            xaxis_title="Year",
            yaxis_title="Renewable Share (%)",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_share, use_container_width=True)

    with col_t2:
        fig_mix = go.Figure()
        fig_mix.add_trace(
            go.Bar(
                x=annual_gen["year"],
                y=annual_gen["renewable_generation_mwh"],
                name="Renewable (MWh)",
                marker_color="#10B981",
            )
        )
        fig_mix.add_trace(
            go.Bar(
                x=annual_gen["year"],
                y=annual_gen["fossil_generation_mwh"],
                name="Fossil Fuels (MWh)",
                marker_color="#64748B",
            )
        )
        fig_mix.update_layout(
            barmode="stack",
            title="Net Generation Volume: Renewable vs Fossil (MWh)",
            xaxis_title="Year",
            yaxis_title="Generation (MWh)",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_mix, use_container_width=True)

    # Technology Breakdown
    st.markdown("#### Generation Breakdown by Generation Technology")
    tech_agg = (
        df_tech_filtered.groupby(["year", "technology_name", "category"])["generation_mwh"]
        .sum()
        .reset_index()
    )
    fig_tech = px.area(
        tech_agg,
        x="year",
        y="generation_mwh",
        color="technology_name",
        title="Generation Evolution by Technology (MWh)",
        labels={"generation_mwh": "Generation (MWh)", "year": "Year", "technology_name": "Technology"},
        template="plotly_white",
    )
    st.plotly_chart(fig_tech, use_container_width=True)


# ==============================================================================
# TAB 2: Sectoral Consumption (Q2)
# ==============================================================================
with tab2:
    st.subheader("Research Question 2: Electricity Consumption by Economic Sector")
    st.caption("Addressing Actor: Energy Planning Lead (Tactical Demand Monitoring)")

    col_s1, col_s2 = st.columns([3, 2])

    with col_s1:
        sector_annual = (
            df_cons_filtered.groupby(["year", "sector_name"])["consumption_mwh"].sum().reset_index()
        )
        fig_sec = px.bar(
            sector_annual,
            x="year",
            y="consumption_mwh",
            color="sector_name",
            title="Annual Final Electricity Consumption by Sector (MWh)",
            labels={"consumption_mwh": "Consumption (MWh)", "year": "Year", "sector_name": "Sector"},
            template="plotly_white",
            barmode="stack",
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    with col_s2:
        latest_year = df_cons_filtered["year"].max()
        df_latest_sector = (
            df_cons_filtered[df_cons_filtered["year"] == latest_year]
            .groupby("sector_name")["consumption_mwh"]
            .sum()
            .reset_index()
        )
        fig_pie = px.pie(
            df_latest_sector,
            values="consumption_mwh",
            names="sector_name",
            title=f"Sector Share in {latest_year}",
            hole=0.4,
            template="plotly_white",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Customer Supply Points (CUPS)
    st.markdown("#### Customer Supply Points (CUPS) Count by Sector")
    cups_agg = df_cons_filtered.groupby(["year", "sector_name"])["customer_cups_count"].sum().reset_index()
    fig_cups = px.line(
        cups_agg,
        x="year",
        y="customer_cups_count",
        color="sector_name",
        title="Evolution of Active Metering Points (CUPS) by Sector",
        labels={"customer_cups_count": "Active CUPS", "year": "Year", "sector_name": "Sector"},
        markers=True,
        template="plotly_white",
    )
    st.plotly_chart(fig_cups, use_container_width=True)


# ==============================================================================
# TAB 3: Grid Efficiency & Losses (Q3)
# ==============================================================================
with tab3:
    st.subheader("Research Question 3: Transmission & Distribution Losses")
    st.caption("Addressing Actor: Insular Grid Operator (Operational Supervision)")

    col_e1, col_e2 = st.columns([1, 1])

    with col_e1:
        annual_loss = (
            df_bal_filtered.groupby("year")[
                ["gross_production_mwh", "internal_demand_mwh", "final_consumption_mwh", "transmission_distribution_losses_mwh"]
            ]
            .sum()
            .reset_index()
        )
        annual_loss["grid_loss_rate_pct"] = (
            annual_loss["transmission_distribution_losses_mwh"] / annual_loss["internal_demand_mwh"] * 100
        ).round(2)

        fig_loss = go.Figure()
        fig_loss.add_trace(
            go.Scatter(
                x=annual_loss["year"],
                y=annual_loss["grid_loss_rate_pct"],
                mode="lines+markers",
                name="Grid Loss Rate (%)",
                line=dict(color="#EF4444", width=3),
                marker=dict(size=8),
            )
        )
        fig_loss.add_hline(
            y=8.0,
            line_dash="dash",
            line_color="#10B981",
            annotation_text="Target Ceiling (8%)",
            annotation_position="top right",
        )
        fig_loss.update_layout(
            title="Grid Loss Rate (%) vs Strategic Target Ceiling",
            xaxis_title="Year",
            yaxis_title="Loss Rate (% of Demand)",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_loss, use_container_width=True)

    with col_e2:
        fig_balance_flow = go.Figure()
        fig_balance_flow.add_trace(
            go.Bar(
                x=annual_loss["year"],
                y=annual_loss["gross_production_mwh"],
                name="Gross Production",
                marker_color="#3B82F6",
            )
        )
        fig_balance_flow.add_trace(
            go.Bar(
                x=annual_loss["year"],
                y=annual_loss["final_consumption_mwh"],
                name="Final Consumption",
                marker_color="#10B981",
            )
        )
        fig_balance_flow.add_trace(
            go.Bar(
                x=annual_loss["year"],
                y=annual_loss["transmission_distribution_losses_mwh"],
                name="Grid Losses",
                marker_color="#EF4444",
            )
        )
        fig_balance_flow.update_layout(
            barmode="group",
            title="Energy Balance Comparison (Production vs Consumption vs Losses)",
            xaxis_title="Year",
            yaxis_title="Energy (MWh)",
            template="plotly_white",
            hovermode="x unified",
        )
        st.plotly_chart(fig_balance_flow, use_container_width=True)


# ==============================================================================
# TAB 4: Architecture & Lineage
# ==============================================================================
with tab4:
    st.subheader("Data Pipeline Architecture & Academic Lineage")
    st.markdown(
        """
        This project implements an end-to-end **ELT Business Intelligence pipeline** adhering to the 
        course specifications of **Business Intelligence (Prof. Pedro A. Toledo, Universidad de La Laguna)**:
        """
    )

    st.markdown(
        """
        | Layer | Technology | Role & Deliverables |
        |---|---|---|
        | **Ingestion (E&L)** | Python (`requests`) | Downloads 5 datasets from ISTAC Operation `C00022A` into PostgreSQL `raw_db.raw`. |
        | **Replication** | Airbyte Community | Replicates source tables from `raw_db` into `analytics_db.raw` with Full Refresh Overwrite. |
        | **Storage (DW)** | PostgreSQL 16 | Dedicated analytics database with schemas: `raw`, `staging`, `intermediate`, `marts`. |
        | **Transform (T)** | dbt Core 1.12 | Enforces dimensional modeling (star schema), model contracts, and 48 automated data tests. |
        | **Orchestration** | Dagster 1.13 | Asset-based DAG coordinating the end-to-end lineage from ingestion to reporting. |
        | **Visual Analytics** | Streamlit + Plotly | Interactive decision-support dashboard answering research questions Q1–Q3. |
        """
    )

    st.info(
        "💡 **dbt Documentation**: View interactive DAG lineage and column dictionary at `http://localhost:8080`."
    )

