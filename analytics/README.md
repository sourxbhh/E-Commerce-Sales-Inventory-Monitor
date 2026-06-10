# Analytics showcase

Standalone SQL over the dbt marts — the kind of analyst-facing work the warehouse
exists to enable. Each file is a single query you can run against the DuckDB
warehouse:

```powershell
duckdb warehouse/olist.duckdb -c ".read analytics/rfm.sql"
```

| File | Technique | Headline |
| --- | --- | --- |
| [`rfm.sql`](rfm.sql) | `NTILE` quintiles, customer segmentation | ~15k "Champions" drive the most revenue, but almost everyone buys once |
| [`cohort_retention.sql`](cohort_retention.sql) | self-join cohorts, `DATE_DIFF` offsets | retention collapses to <1% after the first month |
| [`monthly_revenue_windows.sql`](monthly_revenue_windows.sql) | running total, moving average, MoM growth via `LAG` | strong 2017 growth, seasonal Q4 lift |

**The recurring finding:** Olist is a one-time-purchase marketplace — average
purchase frequency is ~1.05 orders per customer. That reframes the business
question from *retention* to *acquisition + first-order experience* (delivery
speed, review score), which is exactly what `fct_orders` is built to measure.
