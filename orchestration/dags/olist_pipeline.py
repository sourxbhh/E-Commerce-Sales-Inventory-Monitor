"""
Daily Olist warehouse pipeline:

    load_duckdb  ->  dbt_build  ->  ge_validate

Each task shells into the mounted project (/opt/project) and runs the same
entry points used locally. The DAG fails fast: if Great Expectations rejects
the raw data, downstream consumers never see a bad refresh.
"""
from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = os.environ.get("PROJECT_DIR", "/opt/project")

default_args = {
    "owner": "analytics",
    "retries": 1,
}

with DAG(
    dag_id="olist_pipeline",
    description="Load Olist parquet -> DuckDB, build dbt marts, validate with GE.",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["olist", "warehouse", "dbt", "great_expectations"],
) as dag:

    load_duckdb = BashOperator(
        task_id="load_duckdb",
        bash_command=f"cd {PROJECT_DIR} && python -m batch.load_duckdb",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        # --no-partial-parse: the host's target/ partial-parse cache is mounted in
        # and was written by the local (Windows) dbt run; force a clean parse so a
        # scheduled run is deterministic and never trips over a stale manifest.
        bash_command=f"cd {PROJECT_DIR}/warehouse && dbt build --profiles-dir . --no-partial-parse",
    )

    ge_validate = BashOperator(
        task_id="ge_validate",
        bash_command=f"cd {PROJECT_DIR} && python -m quality.validate",
    )

    load_duckdb >> dbt_build >> ge_validate
