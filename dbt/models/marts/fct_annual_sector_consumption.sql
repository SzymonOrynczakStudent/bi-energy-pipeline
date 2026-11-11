with consumption as (
    select * from {{ ref('stg_sector_consumption') }}
),
islands as (
    select * from {{ ref('dim_islands') }}
),
aggregated as (
    select
        c.year,
        c.territory_code,
        c.sector_code,
        c.sector_name,
        sum(case when c.measure_code = 'ENERGIA_ELECTRICA' then c.value else 0 end) as consumption_mwh,
        sum(case when c.measure_code = 'CUPS' then c.value else 0 end) as customer_cups_count
    from consumption c
    group by
        c.year,
        c.territory_code,
        c.sector_code,
        c.sector_name
)

select
    md5(a.year::text || '_' || a.territory_code || '_' || a.sector_code) as sector_consumption_id,
    a.year,
    a.territory_code,
    i.island_name,
    a.sector_code,
    a.sector_name,
    a.consumption_mwh,
    a.customer_cups_count
from aggregated a
join islands i on a.territory_code = i.territory_code

