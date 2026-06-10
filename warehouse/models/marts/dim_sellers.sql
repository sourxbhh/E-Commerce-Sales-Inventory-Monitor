with sellers as (
    select * from {{ ref('stg_olist__sellers') }}
),

geo as (
    select * from {{ ref('stg_olist__geolocation') }}
)

select
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    g.latitude  as seller_latitude,
    g.longitude as seller_longitude
from sellers as s
left join geo as g
    on s.seller_zip_code_prefix = g.zip_code_prefix
