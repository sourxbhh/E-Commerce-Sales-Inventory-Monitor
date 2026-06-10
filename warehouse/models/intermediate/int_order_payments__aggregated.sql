-- Collapse payments to one row per order: total paid, installments, methods.
with payments as (
    select * from {{ ref('stg_olist__order_payments') }}
)

select
    order_id,
    sum(payment_value)        as payment_value,
    max(payment_installments) as max_installments,
    count(*)                  as n_payments,
    -- distinct payment methods used on the order, comma-joined
    string_agg(distinct payment_type, ',' order by payment_type) as payment_types
from payments
group by 1
