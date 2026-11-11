with generation as (
    select * from {{ ref('stg_electricity_generation') }}
),
aggregated as (
    select
        period_code,
        year,
        month,
        territory_code,
        sum(case when is_renewable then generation_mwh else 0 end) as renewable_generation_mwh,
        sum(case when not is_renewable then generation_mwh else 0 end) as fossil_generation_mwh,
        sum(generation_mwh) as total_generation_mwh
    from generation
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
    renewable_generation_mwh,
    fossil_generation_mwh,
    total_generation_mwh,
    case
        when total_generation_mwh > 0 then
            round((renewable_generation_mwh / total_generation_mwh) * 100.0, 2)
        else 0
    end as renewable_share_pct
from aggregated

