with historical_data as (
    select
        "TIME_PERIOD_CODE",
        "TERRITORIO_CODE",
        "TERRITORIO_es",
        "FLUJO_ENERGIA_CODE",
        "FLUJO_ENERGIA_es",
        "MEDIDAS_CODE",
        "OBS_VALUE",
        "_loaded_at",
        "_airbyte_extracted_at"
    from {{ source('istac', 'c00022a_000001') }}
),
recent_data as (
    select
        "TIME_PERIOD_CODE",
        "TERRITORIO_CODE",
        "TERRITORIO_es",
        "FLUJO_ENERGIA_CODE",
        "FLUJO_ENERGIA_es",
        "MEDIDAS_CODE",
        "OBS_VALUE",
        "_loaded_at",
        "_airbyte_extracted_at"
    from {{ source('istac', 'c00022a_000002') }}
),
unified as (
    select * from historical_data
    union all
    select * from recent_data
)

select
    "TIME_PERIOD_CODE"::integer as year,
    "TERRITORIO_CODE" as territory_code,
    trim("TERRITORIO_es") as territory_name,
    "FLUJO_ENERGIA_CODE" as sector_code,
    trim("FLUJO_ENERGIA_es") as sector_name,
    "MEDIDAS_CODE" as measure_code,
    coalesce(nullif("OBS_VALUE", '')::numeric, 0) as value,
    "_loaded_at"::timestamptz as loaded_at,
    "_airbyte_extracted_at" as airbyte_extracted_at
from unified
where "MEDIDAS_CODE" in ('ENERGIA_ELECTRICA', 'CUPS')
  and "FLUJO_ENERGIA_CODE" != 'FC'  -- Exclude aggregate 'Final consumption' to avoid double counting
