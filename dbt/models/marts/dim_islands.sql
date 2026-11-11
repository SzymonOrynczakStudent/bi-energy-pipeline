with islands as (
    select * from {{ ref('canary_islands') }}
)

select
    territory_code,
    island_name,
    province,
    grid_system
from islands

