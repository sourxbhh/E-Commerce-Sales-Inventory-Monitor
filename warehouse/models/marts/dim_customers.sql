with customers as (
    select * from {{ ref('stg_olist__customers') }}
),

geo as (
    select * from {{ ref('stg_olist__geolocation') }}
)

select
    c.customer_id,
    c.customer_unique_id,
    c.customer_zip_code_prefix,
    c.customer_city,
    c.customer_state,
    g.latitude  as customer_latitude,
    g.longitude as customer_longitude
from customers as c
left join geo as g
    on c.customer_zip_code_prefix = g.zip_code_prefix
