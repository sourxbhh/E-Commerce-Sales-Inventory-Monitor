-- RFM segmentation over delivered orders, keyed by customer_unique_id (the
-- field that ties repeat buyers together; customer_id is per-order).
--
-- Recency  = days since the customer's last purchase (vs. the latest in the data)
-- Frequency = number of orders
-- Monetary  = total order value
-- Each is bucketed into quintiles (1..5) with NTILE; the segment label is a
-- common RFM heuristic. Returns the segment distribution.
--
--   duckdb warehouse/olist.duckdb -c ".read analytics/rfm.sql"
with orders as (
    select
        customer_unique_id,
        purchase_date,
        order_value
    from main_marts.fct_orders
    where order_status = 'delivered'
),

bounds as (select max(purchase_date) as as_of from orders),

per_customer as (
    select
        o.customer_unique_id,
        date_diff('day', max(o.purchase_date), b.as_of) as recency_days,
        count(*)                                        as frequency,
        sum(o.order_value)                              as monetary
    from orders as o
    cross join bounds as b
    group by o.customer_unique_id, b.as_of
),

scored as (
    select
        *,
        -- low recency = better, so reverse the ntile
        6 - ntile(5) over (order by recency_days)      as r,
        ntile(5) over (order by frequency, monetary)   as f,
        ntile(5) over (order by monetary)              as m
    from per_customer
),

labelled as (
    select
        *,
        case
            when r >= 4 and f >= 4 then 'Champions'
            when r >= 4 and f <= 2 then 'New / Promising'
            when r <= 2 and f >= 4 then 'At Risk'
            when r <= 2 and f <= 2 then 'Hibernating'
            else 'Loyal / Potential'
        end as segment
    from scored
)

select
    segment,
    count(*)                              as customers,
    round(avg(recency_days), 1)           as avg_recency_days,
    round(avg(frequency), 2)              as avg_frequency,
    round(avg(monetary), 2)               as avg_monetary,
    round(sum(monetary), 2)               as total_monetary
from labelled
group by segment
order by total_monetary desc;
