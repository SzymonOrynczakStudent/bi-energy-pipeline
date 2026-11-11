with technologies as (
    select * from {{ ref('energy_technologies') }}
)

select
    technology_code,
    technology_name,
    category,
    is_renewable
from technologies

