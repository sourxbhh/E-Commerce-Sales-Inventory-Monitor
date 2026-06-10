-- Grain: one row per order. Joins customer, item aggregates, payment aggregates,
-- and review score, plus derived delivery / lead-time metrics.
with orders as (
    select * from {{ ref('stg_olist__orders') }}
),

items as (
    select * from {{ ref('int_order_items__aggregated') }}
),

payments as (
    select * from {{ ref('int_order_payments__aggregated') }}
),

reviews as (
    -- a few orders carry multiple reviews; keep the latest
    select
        order_id,
        review_score,
        row_number() over (partition by order_id order by created_at desc) as rn
    from {{ ref('stg_olist__order_reviews') }}
),

customers as (
    select * from {{ ref('stg_olist__customers') }}
)

select
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,

    o.purchased_at,
    o.approved_at,
    o.delivered_customer_at,
    o.estimated_delivery_at,
    cast(o.purchased_at as date) as purchase_date,

    coalesce(i.n_items, 0)             as n_items,
    coalesce(i.n_distinct_products, 0) as n_distinct_products,
    coalesce(i.n_sellers, 0)           as n_sellers,
    coalesce(i.items_value, 0)         as items_value,
    coalesce(i.freight_value, 0)       as freight_value,
    coalesce(i.order_value, 0)         as order_value,

    p.payment_value,
    p.max_installments,
    p.payment_types,

    r.review_score,

    -- delivery lead time in days (null until delivered)
    date_diff(
        'day', o.purchased_at, o.delivered_customer_at
    ) as delivery_days,
    -- positive => delivered before the estimate
    date_diff(
        'day', o.delivered_customer_at, o.estimated_delivery_at
    ) as delivery_vs_estimate_days,
    case
        when o.delivered_customer_at is not null
             and o.delivered_customer_at > o.estimated_delivery_at
        then true
        else false
    end as is_late
from orders as o
left join customers as c on o.customer_id = c.customer_id
left join items as i     on o.order_id = i.order_id
left join payments as p  on o.order_id = p.order_id
left join reviews as r   on o.order_id = r.order_id and r.rn = 1
