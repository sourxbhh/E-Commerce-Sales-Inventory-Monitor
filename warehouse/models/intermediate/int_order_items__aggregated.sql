-- Collapse order_items to one row per order: item count + money totals.
with items as (
    select * from {{ ref('stg_olist__order_items') }}
)

select
    order_id,
    count(*)             as n_items,
    count(distinct product_id) as n_distinct_products,
    count(distinct seller_id)  as n_sellers,
    sum(price)           as items_value,
    sum(freight_value)   as freight_value,
    sum(price) + sum(freight_value) as order_value
from items
group by 1
