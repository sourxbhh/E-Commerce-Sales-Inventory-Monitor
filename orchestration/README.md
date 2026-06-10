# M4 — Airflow orchestration + Great Expectations

Airflow runs the daily warehouse refresh; Great Expectations gates it.

```
load_duckdb  ──►  dbt_build  ──►  ge_validate
(parquet→DuckDB)  (staging→marts)  (GE on raw.*; fails the run on bad data)
```

Airflow doesn't support native Windows, so it runs in Docker (LocalExecutor +
Postgres). The repo root is mounted at `/opt/project`, so DAG tasks execute the
same entry points (`batch.load_duckdb`, `dbt build`, `quality.validate`) as the
local dev box, against the same `warehouse/olist.duckdb`.

## Run

```powershell
# build the image (Airflow + dbt + duckdb + GE)
docker compose -f docker/airflow/docker-compose.yml build

# one-time: init metadata db + admin user
docker compose -f docker/airflow/docker-compose.yml up airflow-init

# start webserver + scheduler
docker compose -f docker/airflow/docker-compose.yml up -d
# UI: http://localhost:8080  (airflow / airflow)  — unpause + trigger "olist_pipeline"
```

## Quick smoke test (no webserver/scheduler needed)

Runs the whole DAG once in an ephemeral container:

```powershell
docker compose -f docker/airflow/docker-compose.yml run --rm airflow-scheduler `
  bash -c "airflow db migrate && airflow dags test olist_pipeline 2024-01-01"
```

Tear down: `docker compose -f docker/airflow/docker-compose.yml down -v`.

## Standalone GE

`python -m quality.validate` validates `raw.*` directly and exits non-zero on
failure — handy in CI without Airflow.
```
