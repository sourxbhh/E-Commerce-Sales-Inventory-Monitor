# M5 — FastAPI metrics API

Read-only KPI service over the dbt marts in DuckDB. Same numbers the Power BI
report binds to, exposed as JSON.

## Run

```powershell
uvicorn api.main:app --reload --port 8000
# interactive docs: http://localhost:8000/docs
```

Requires the marts built first (M2): `python -m batch.load_duckdb` + `dbt build`.

## Endpoints

| Endpoint | Returns |
| --- | --- |
| `GET /health` | service status + `fct_orders` row count |
| `GET /kpis` | totals: orders, revenue, AOV, avg review, avg delivery days, late % |
| `GET /kpis/by-state` | orders / revenue / avg review per customer state |
| `GET /kpis/monthly` | orders / revenue per purchase month |
| `GET /kpis/top-categories?limit=N` | top product categories by revenue |
