with source_data as (
    select * from {{ source('istac', 'c00022a_000008') }}
)

select
    "TIME_PERIOD_CODE" as period_code,
    substring("TIME_PERIOD_CODE" from 1 for 4)::integer as year,
    substring("TIME_PERIOD_CODE" from 7 for 2)::integer as month,
    "TERRITORIO_CODE" as territory_code,
    trim("TERRITORIO#es") as territory_name,
    "PRODUCTO_ENERGETICO_CODE" as technology_code,
    trim("PRODUCTO_ENERGETICO#es") as source_technology_name,
    case
        when "PRODUCTO_ENERGETICO_CODE" in ('RA300', 'RA420', 'RA100', 'RA100_RA300', 'R5300') then true
        else false
    end as is_renewable,
    coalesce(nullif("OBS_VALUE", '')::numeric, 0) as generation_mwh,
    "_loaded_at"::timestamptz as loaded_at
from source_data
where "MEDIDAS_CODE" = 'ENERGIA_ELECTRICA'
  and "PRODUCTO_ENERGETICO_CODE" not in ('_T', 'RA000')  -- Exclude aggregates to prevent double counting
  and "TIME_PERIOD_CODE" like '%-M%'                   -- Enforce homogeneous monthly grain

