with balance as (
    select * from {{ ref('stg_electricity_balance') }}
),
pivoted as (
    select
        period_code,
        year,
        month,
        territory_code,
        sum(case when flow_code = 'GEP' then energy_mwh else 0 end) as gross_production_mwh,
        sum(case when flow_code = 'ID' then energy_mwh else 0 end) as internal_demand_mwh,
        sum(case when flow_code = 'AFC' then energy_mwh else 0 end) as final_consumption_mwh
    from balance
    group by
        period_code,
        year,
        month,
        territory_code
)

select
    period_code,
    year,
    month,
    territory_code,
    gross_production_mwh,
    internal_demand_mwh,
    final_consumption_mwh,
    greatest(gross_production_mwh - final_consumption_mwh, 0) as transmission_distribution_losses_mwh,
    case
        when gross_production_mwh > 0 then
            round(((gross_production_mwh - final_consumption_mwh) / gross_production_mwh) * 100.0, 2)
        else 0
    end as grid_loss_rate_pct
from pivoted

