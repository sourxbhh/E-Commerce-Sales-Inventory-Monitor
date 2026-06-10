# M3 — Kafka replay + Spark Structured Streaming

Simulates a live order stream: rows from the DuckDB `raw` schema are replayed
onto Kafka, and a Spark Structured Streaming job consumes them.

```
DuckDB raw.orders ──► ingestion.kafka_replay ──► Kafka (olist.orders) ──► streaming.spark_consumer
```

## Prerequisites

- **Docker Desktop** running (hosts the single-node Kafka broker).
- **JDK 17** with `JAVA_HOME` set (Spark requirement). Install once:
  `winget install -e --id EclipseAdoptium.Temurin.17.JDK`
- DuckDB warehouse built (M2): `python -m batch.load_duckdb`.

## Run (three terminals)

```powershell
# 1. broker
docker compose -f docker/docker-compose.yml up -d

# 2. consumer — event-time windowed order counts by status (downloads the
#    Kafka connector jar on first run)
python -m streaming.spark_consumer            # --mode raw to land parquet instead

# 3. producer — replay orders at 50 msg/s (event-time ordered)
python -m ingestion.kafka_replay              # --table order_items|order_payments, --rate, --limit
```

Tear down: `docker compose -f docker/docker-compose.yml down`.
