"""
FastAPI metrics service over the dbt marts in DuckDB.

Read-only: opens the warehouse file in read_only mode and serves KPI rollups
straight from main_marts.* / main_staging.*. Same numbers the Power BI report
binds to, exposed as JSON.

Run:
    uvicorn api.main:app --reload --port 8000
    # or: python -m api.main
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import duckdb
from fastapi import FastAPI, Query

from ingestion.config import settings

MARTS = "main_marts"
STAGING = "main_staging"

_con: duckdb.DuckDBPyConnection | None = None


def _query(sql: str, params: list | None = None) -> list[dict]:
    # cursor() returns an isolated connection to the same db — safe to call from
    # FastAPI's threadpool without sharing one cursor across threads.
    cur = _con.cursor()
    rel = cur.execute(sql, params or [])
    cols = [d[0] for d in rel.description]
    return [dict(zip(cols, row, strict=False)) for row in rel.fetchall()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _con  # noqa: PLW0603 — app-level singleton set once in lifespan
    if not settings.duckdb_path.exists():
        raise RuntimeError(
            f"{settings.duckdb_path} not found — run `python -m batch.load_duckdb` "
            f"and `dbt build` first."
        )
    _con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    yield
    _con.close()


app = FastAPI(
    title="Olist Analytics API",
    description="KPI rollups over the Olist dbt marts (DuckDB).",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict:
    return {"service": "olist-analytics-api", "docs": "/docs"}


@app.get("/health")
def health() -> dict:
    n = _query(f"select count(*) as n from {MARTS}.fct_orders")[0]["n"]
    return {"status": "ok", "fct_orders_rows": n}


@app.get("/kpis")
def kpis() -> dict:
    return _query(f"""
        select
            count(*)                                          as total_orders,
            round(sum(order_value), 2)                        as total_revenue,
            round(avg(order_value), 2)                        as avg_order_value,
            round(avg(review_score), 3)                       as avg_review_score,
            round(avg(delivery_days) filter (where order_status = 'delivered'), 2)
                                                              as avg_delivery_days,
            round(100.0 * avg(case when is_late then 1 else 0 end)
                  filter (where order_status = 'delivered'), 2) as pct_late
        from {MARTS}.fct_orders
    """)[0]


@app.get("/kpis/by-state")
def by_state() -> list[dict]:
    return _query(f"""
        select
            customer_state,
            count(*)                   as orders,
            round(sum(order_value), 2) as revenue,
            round(avg(review_score), 3) as avg_review_score
        from {MARTS}.fct_orders
        group by customer_state
        order by revenue desc
    """)


@app.get("/kpis/monthly")
def monthly() -> list[dict]:
    return _query(f"""
        select
            date_trunc('month', purchase_date) as month,
            count(*)                           as orders,
            round(sum(order_value), 2)         as revenue
        from {MARTS}.fct_orders
        where purchase_date is not null
        group by 1
        order by 1
    """)


@app.get("/kpis/top-categories")
def top_categories(limit: int = Query(10, ge=1, le=100)) -> list[dict]:
    return _query(f"""
        select
            dp.product_category,
            count(*)                  as items_sold,
            round(sum(oi.price), 2)   as revenue
        from {STAGING}.stg_olist__order_items as oi
        join {MARTS}.dim_products as dp using (product_id)
        where dp.product_category is not null
        group by 1
        order by revenue desc
        limit ?
    """, [limit])


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
