-- Monthly cohort retention: group customers by the month of their first order,
-- then measure how many return in each subsequent month. Olist is dominated by
-- one-time buyers, so retention drops off fast — that low repeat rate is itself
-- the headline finding.
--
--   duckdb warehouse/olist.duckdb -c ".read analytics/cohort_retention.sql"
with orders as (
    select
        customer_unique_id,
        date_trunc('month', purchase_date) as order_month
    from main_marts.fct_orders
    where order_status = 'delivered' and purchase_date is not null
),

cohorts as (
    select
        customer_unique_id,
        min(order_month) as cohort_month
    from orders
    group by customer_unique_id
),

activity as (
    select distinct
        c.cohort_month,
        o.customer_unique_id,
        date_diff('month', c.cohort_month, o.order_month) as month_offset
    from orders as o
    join cohorts as c using (customer_unique_id)
),

cohort_size as (
    select cohort_month, count(*) as n_customers
    from cohorts
    group by cohort_month
)

select
    a.cohort_month,
    s.n_customers                                          as cohort_size,
    a.month_offset,
    count(*)                                               as active,
    round(100.0 * count(*) / s.n_customers, 2)             as retention_pct
from activity as a
join cohort_size as s using (cohort_month)
where a.month_offset between 0 and 6
group by a.cohort_month, s.n_customers, a.month_offset
order by a.cohort_month, a.month_offset;
