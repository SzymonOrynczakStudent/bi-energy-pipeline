with generation as (
    select * from {{ ref('int_monthly_generation') }}
),
islands as (
    select * from {{ ref('dim_islands') }}
)

select
    md5(g.period_code || '_' || g.territory_code) as generation_id,
    g.period_code,
    g.year,
    g.month,
    to_date(g.year || '-' || lpad(g.month::text, 2, '0') || '-01', 'YYYY-MM-DD') as date,
    g.territory_code,
    i.island_name,
    i.province,
    i.grid_system,
    g.renewable_generation_mwh,
    g.fossil_generation_mwh,
    g.total_generation_mwh,
    g.renewable_share_pct
from generation g
join islands i on g.territory_code = i.territory_code

