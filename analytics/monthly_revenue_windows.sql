-- Window-function showcase: monthly revenue with a running total, a 3-month
-- moving average, and month-over-month growth %.
--
--   duckdb warehouse/olist.duckdb -c ".read analytics/monthly_revenue_windows.sql"
with monthly as (
    select
        date_trunc('month', purchase_date) as month,
        count(*)                           as orders,
        sum(order_value)                   as revenue
    from main_marts.fct_orders
    where purchase_date is not null
    group by 1
)

select
    month,
    orders,
    round(revenue, 2) as revenue,
    round(sum(revenue) over (order by month), 2) as revenue_running_total,
    round(avg(revenue) over (order by month rows between 2 preceding and current row), 2)
        as revenue_3mo_moving_avg,
    round(
        100.0 * (revenue - lag(revenue) over (order by month))
        / nullif(lag(revenue) over (order by month), 0),
        1
    ) as revenue_mom_pct
from monthly
order by month;
