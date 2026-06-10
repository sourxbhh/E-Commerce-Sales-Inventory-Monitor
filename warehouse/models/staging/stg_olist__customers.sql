with source as (
    select * from {{ source('raw', 'customers') }}
)

select
    customer_id,
    customer_unique_id,
    cast(customer_zip_code_prefix as varchar) as customer_zip_code_prefix,
    customer_city,
    customer_state
from source
