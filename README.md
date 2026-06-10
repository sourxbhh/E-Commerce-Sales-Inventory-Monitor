# Olist E-Commerce Analytics Platform

End-to-end analytics platform on the public **Brazilian Olist** e-commerce dataset (~100k orders, 9 relational tables). Built as a portfolio piece covering the modern data stack a Data Analyst / Analytics Engineer job description asks for.

## Stack & keyword index

| Layer            | Tech                                                                                         |
| ---------------- | -------------------------------------------------------------------------------------------- |
| Object storage   | **Azure Data Lake Storage Gen2** (provisioned via **Terraform** `azurerm`), partitioned Parquet |
| Streaming        | **Apache Kafka**, **Spark Structured Streaming** (`confluent-kafka` producer)                |
| Batch ingestion  | Python + **boto3** + **pyarrow**                                                             |
| Warehouse        | **DuckDB** (local), **Snowflake**-ready (swap dbt profile)                                   |
| Transformations  | **dbt** — staging → intermediate → marts                                                     |
| Data quality     | **Great Expectations** + dbt tests                                                           |
| Orchestration    | **Apache Airflow** (LocalExecutor, Docker)                                                   |
| Serving          | **FastAPI** metrics API                                                                      |
| BI / dashboard   | **Power BI** (.pbix on DuckDB ODBC) + Metabase fallback                                      |
| CI/CD            | **GitHub Actions** — ruff, sqlfluff, pytest, dbt build, GE, Docker → GHCR                    |
| Containerization | **Docker** + Docker Compose                                                                  |

## Architecture

```
Olist CSVs (Kaggle)
        │ one-shot
        ▼
   Azure ADLS Gen2 (raw zone, partitioned parquet) ──── Terraform-provisioned
        │
   ┌────┴─────────────┐
   │                  │
 stream             batch (daily)
   │                  │
 Kafka              Airflow DAG
   │                  │
 Spark              boto3 + DuckDB
   │                  │
   └────────┬─────────┘
            ▼
       raw.* schema  ──►  dbt (staging → marts)  ──►  marts.fct_orders, dim_*, rfm, cohorts
                                   │
                                   ├──► FastAPI /kpis
                                   └──► Power BI / Metabase
```

## Repository layout

```
ingestion/      # Olist CSV → parquet → S3, plus the Kafka replay producer
streaming/      # Spark Structured Streaming consumer
batch/          # Daily S3 → DuckDB batch loader
warehouse/      # dbt project (models, tests, seeds)
orchestration/  # Airflow DAGs
quality/        # Great Expectations suites
api/            # FastAPI metrics endpoints
analytics/      # Standalone showcase SQL (window fns, cohorts, RFM)
dashboard/      # Power BI .pbix + connection files
infra/          # Terraform for ADLS Gen2 + RBAC
docker/         # docker-compose.yml (Kafka, Airflow, etc.)
.github/        # CI/CD workflows
```

## Roadmap

- [x] **M0** Wipe + baseline scaffolding
- [x] **M1** Olist → parquet → ADLS Gen2, Terraform `azurerm` module
- [x] **M2** DuckDB warehouse + dbt models + tests
- [ ] **M3** Kafka replay producer + Spark streaming consumer
- [ ] **M4** Airflow DAG + Great Expectations
- [ ] **M5** FastAPI + Power BI dashboard
- [ ] **M6** GitHub Actions CI/CD
- [ ] **M7** Polish, screenshots, writeup

See [`CLAUDE.md`](CLAUDE.md) for agent / contributor guidance.

## Quickstart (placeholder — populated as milestones land)

```bash
python -m venv .venv && . .venv/Scripts/activate    # Windows
pip install -r requirements.txt
cp .env.example .env                                 # fill in Azure + Kaggle creds
# milestone-specific commands land in each section below as they're built
```
