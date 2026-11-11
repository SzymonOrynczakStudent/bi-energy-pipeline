with balance as (
    select * from {{ ref('int_balance_efficiency') }}
),
islands as (
    select * from {{ ref('dim_islands') }}
)

select
    md5(b.period_code || '_' || b.territory_code) as balance_id,
    b.period_code,
    b.year,
    b.month,
    to_date(b.year || '-' || lpad(b.month::text, 2, '0') || '-01', 'YYYY-MM-DD') as date,
    b.territory_code,
    i.island_name,
    b.gross_production_mwh,
    b.internal_demand_mwh,
    b.final_consumption_mwh,
    b.transmission_distribution_losses_mwh,
    b.grid_loss_rate_pct
from balance b
join islands i on b.territory_code = i.territory_code

