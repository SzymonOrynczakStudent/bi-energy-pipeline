with source_data as (
    select * from {{ source('istac', 'c00022a_000004') }}
)

select
    "TIME_PERIOD_CODE" as period_code,
    substring("TIME_PERIOD_CODE" from 1 for 4)::integer as year,
    substring("TIME_PERIOD_CODE" from 7 for 2)::integer as month,
    "TERRITORIO_CODE" as territory_code,
    trim("TERRITORIO#es") as territory_name,
    "FLUJO_ENERGIA_CODE" as flow_code,
    trim("FLUJO_ENERGIA#es") as flow_name,
    coalesce(nullif("OBS_VALUE", '')::numeric, 0) as energy_mwh,
    "_loaded_at"::timestamptz as loaded_at
from source_data
where "MEDIDAS_CODE" = 'ENERGIA_ELECTRICA'
  and "TIME_PERIOD_CODE" like '%-M%'  -- Enforce homogeneous monthly grain

