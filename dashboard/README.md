# M5 — Power BI dashboard

The report binds to the dbt marts (`fct_orders`, `dim_customers`, `dim_products`,
`dim_sellers`) in DuckDB. The `.pbix` itself is binary and isn't committed; this
folder holds everything needed to rebuild it deterministically.

| File | Purpose |
| --- | --- |
| [`connection.pbids`](connection.pbids) | Power BI data source — DuckDB over ODBC (Import). Edit the `Database=` path. |
| [`power_query.m`](power_query.m) | Power Query (M) to load each mart table. Set the `DbPath` parameter. |
| [`measures.dax`](measures.dax) | DAX measures (revenue, AOV, review, delivery, late %, time intelligence). |
| [`theme.json`](theme.json) | Report theme (colors / fonts). |

## Prerequisites

- **Power BI Desktop** (Windows).
- **DuckDB ODBC driver** — install from the DuckDB site, then either point
  `connection.pbids` at `warehouse/olist.duckdb` or register a DSN named `olist`.
- Marts built: `python -m batch.load_duckdb` then `dbt build` (M2).

## Build steps

1. Open `connection.pbids` (or *Get Data → ODBC*), fix the database path.
2. Import `main_marts.fct_orders`, `dim_customers`, `dim_products`, `dim_sellers`.
3. Model: relate `fct_orders[customer_id] → dim_customers[customer_id]`,
   `…[product_id]` is on `order_items`, so for category visuals import
   `main_staging.stg_olist__order_items` too. Add a Date table on `purchase_date`.
4. Paste measures from `measures.dax`. Apply `theme.json` (*View → Themes → Browse*).

## Suggested pages

1. **Executive** — cards (Total Revenue, Orders, AOV, Avg Review, Late %),
   revenue trend by month, revenue by state (map).
2. **Delivery** — Avg Delivery Days by state, late % distribution, delivery vs
   estimate histogram.
3. **Products** — top categories by revenue, review score by category.

## No Power BI? Two fallbacks

- **API** — the same KPIs are served as JSON by the FastAPI app
  (`uvicorn api.main:app`); see [api/](../api). Power BI can also bind to it via
  *Web.Contents* instead of ODBC.
- **Metabase** — point a DuckDB connection at the same file for a web dashboard.
