"""Quick health check: MySQL connectivity, seed row counts, Kafka broker."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mysql.connector
from confluent_kafka.admin import AdminClient

from generator.config import KAFKA, MYSQL


def check_mysql() -> None:
    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    cur = conn.cursor()
    for table in ("products", "kpi_thresholds"):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"[mysql] {table}: {count} rows")
    conn.close()


def check_kafka() -> None:
    admin = AdminClient({"bootstrap.servers": KAFKA.bootstrap_servers})
    md = admin.list_topics(timeout=5)
    topics = list(md.topics.keys())
    print(f"[kafka] topics: {topics}")
    for t in (KAFKA.orders_topic, KAFKA.inventory_topic):
        status = "OK" if t in topics else "MISSING"
        print(f"[kafka] {t}: {status}")


if __name__ == "__main__":
    print(f"MySQL target: {MYSQL.host}:{MYSQL.port}/{MYSQL.database}")
    check_mysql()
    print(f"Kafka target: {KAFKA.bootstrap_servers}")
    check_kafka()
    print("Verification complete.")
