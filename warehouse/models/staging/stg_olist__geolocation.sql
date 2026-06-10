-- Geolocation has many rows per zip prefix; dedupe to one representative
-- centroid per prefix so downstream joins stay 1:1.
with source as (
    select * from {{ source('raw', 'geolocation') }}
)

select
    cast(geolocation_zip_code_prefix as varchar) as zip_code_prefix,
    avg(cast(geolocation_lat as double))         as latitude,
    avg(cast(geolocation_lng as double))         as longitude,
    any_value(geolocation_city)                  as city,
    any_value(geolocation_state)                 as state
from source
group by 1
