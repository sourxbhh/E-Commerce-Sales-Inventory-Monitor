# Airflow image + the analytics libraries the DAG tasks need (dbt, duckdb, GE).
FROM apache/airflow:2.10.3-python3.11

COPY requirements-airflow.txt /requirements-airflow.txt
RUN pip install --no-cache-dir -r /requirements-airflow.txt
