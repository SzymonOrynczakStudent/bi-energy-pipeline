-- Singular test: Verifies that the sum of renewable and fossil generation matches total generation.
-- In dbt, a test passes when the query returns 0 rows.
with balance_check as (
    select
        generation_id,
        total_generation_mwh,
        (renewable_generation_mwh + fossil_generation_mwh) as sum_components,
        abs(total_generation_mwh - (renewable_generation_mwh + fossil_generation_mwh)) as difference
    from {{ ref('fct_monthly_generation') }}
)

select *
from balance_check
where difference > 0.01

