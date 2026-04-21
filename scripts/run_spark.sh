#!/usr/bin/env bash
# Launch the Spark Structured Streaming job with the right connectors.
set -e
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

spark-submit \
    --packages "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,com.mysql:mysql-connector-j:8.4.0" \
    --conf spark.sql.session.timeZone=UTC \
    streaming/stream_processor.py
