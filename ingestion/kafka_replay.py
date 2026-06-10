"""
Replay Olist rows from the DuckDB `raw` schema onto Kafka topics, simulating a
live event stream. Each row is one message: key = order_id, value = JSON.

Orders are replayed in event-time order (order_purchase_timestamp) so the Spark
consumer's windowed aggregations look realistic.

Run (broker must be up — see docker/docker-compose.yml):
    python -m ingestion.kafka_replay                      # orders, 50 msg/s
    python -m ingestion.kafka_replay --table order_items
    python -m ingestion.kafka_replay --rate 0 --limit 1000   # full speed, capped
"""
from __future__ import annotations

import argparse
import json
import logging
import time

import duckdb
from confluent_kafka import Producer

from ingestion.config import settings

log = logging.getLogger("kafka_replay")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s")

# table -> (topic, order-by column for event-time replay)
TABLES = {
    "orders": (settings.kafka_topic_orders, "order_purchase_timestamp"),
    "order_items": (settings.kafka_topic_order_items, "shipping_limit_date"),
    "order_payments": (settings.kafka_topic_payments, None),
}


def _rows(table: str, order_by: str | None, limit: int | None):
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    sql = f"SELECT * FROM {settings.warehouse_schema_raw}.{table}"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit:
        sql += f" LIMIT {limit}"
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        yield dict(zip(cols, row, strict=False))
    con.close()


def _delivery(err, msg) -> None:
    if err is not None:
        log.error("delivery failed: %s", err)


def replay(table: str, rate: float, limit: int | None) -> None:
    if table not in TABLES:
        raise SystemExit(f"unknown table {table!r}; choose from {list(TABLES)}")
    topic, order_by = TABLES[table]

    producer = Producer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "client.id": "olist-replay",
        "linger.ms": 50,
    })

    interval = 1.0 / rate if rate and rate > 0 else 0.0
    n = 0
    for record in _rows(table, order_by, limit):
        key = str(record.get("order_id", "")).encode()
        value = json.dumps(record, default=str).encode()
        producer.produce(topic, key=key, value=value, on_delivery=_delivery)
        producer.poll(0)
        n += 1
        if n % 1000 == 0:
            log.info("produced %s messages -> %s", f"{n:,}", topic)
        if interval:
            time.sleep(interval)

    producer.flush()
    log.info("done. produced %s messages -> %s", f"{n:,}", topic)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default="orders", choices=list(TABLES))
    ap.add_argument("--rate", type=float, default=50.0, help="messages/sec; 0 = unlimited")
    ap.add_argument("--limit", type=int, default=None, help="cap number of messages")
    args = ap.parse_args()
    replay(args.table, args.rate, args.limit)


if __name__ == "__main__":
    main()
