"""
On-demand demo triggers -- feeds the pipeline with scripted events
so the Power BI dashboard has something to react to on camera.

    python scripts/demo_controller.py burst --size 60 --duration 15
        -> publish a flash-sale burst to Kafka directly; the Spark
           job will aggregate it and the anomaly detector will flag
           the revenue spike.

    python scripts/demo_controller.py drain --product 1001 --times 50
        -> publish repeated orders for a specific SKU until stock
           crosses the reorder threshold, triggering a LOW_STOCK
           alert.

    python scripts/demo_controller.py clear-alerts
        -> mark all alerts as resolved (for a clean demo reset).
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from confluent_kafka import Producer
import mysql.connector

from generator.config import KAFKA, MYSQL
from generator.product_catalog import load_products


def _producer() -> Producer:
    return Producer({"bootstrap.servers": KAFKA.bootstrap_servers, "linger.ms": 10})


def _publish(prod: Producer, order: dict) -> None:
    prod.produce(
        topic=KAFKA.orders_topic,
        key=order["order_id"].encode(),
        value=json.dumps(order).encode(),
    )
    prod.poll(0)


def _build_order(items_spec: list[dict]) -> dict:
    total = sum(it["unit_price"] * it["quantity"] for it in items_spec)
    return {
        "order_id": str(uuid.uuid4()),
        "customer_id": f"DEMO-{random.randint(1, 9999):04d}",
        "order_timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "total_amount": round(total, 2),
        "item_count": sum(it["quantity"] for it in items_spec),
        "items": items_spec,
        "status": "CREATED",
    }


# ---------------------------------------------------------------------------
# burst
# ---------------------------------------------------------------------------

def cmd_burst(size: int, duration: float) -> None:
    products = load_products()
    if not products:
        print("No products loaded; seed DB first.")
        sys.exit(1)
    prod = _producer()
    delay = duration / max(size, 1)
    print(f">> bursting {size} orders in {duration}s (~{delay:.2f}s apart)")
    for i in range(size):
        picks = random.choices(
            products,
            weights=[p.popularity_weight for p in products],
            k=random.randint(2, 5),
        )
        items = [
            {
                "product_id": p.product_id,
                "product_name": p.name,
                "category": p.category,
                "quantity": random.randint(1, 3),
                "unit_price": round(p.price, 2),
                "line_total": round(p.price * random.randint(1, 3), 2),
            }
            for p in picks
        ]
        _publish(prod, _build_order(items))
        if (i + 1) % 10 == 0:
            print(f"  sent {i + 1}/{size}")
        time.sleep(delay)
    prod.flush(10)
    print("burst complete")


# ---------------------------------------------------------------------------
# drain
# ---------------------------------------------------------------------------

def cmd_drain(product_id: int, times: int, qty_per_order: int) -> None:
    products = {p.product_id: p for p in load_products()}
    target = products.get(product_id)
    if target is None:
        print(f"Unknown product_id {product_id}")
        sys.exit(1)
    prod = _producer()
    print(
        f">> draining product {product_id} ({target.name}): "
        f"{times} orders x {qty_per_order} units"
    )
    for i in range(times):
        items = [
            {
                "product_id": target.product_id,
                "product_name": target.name,
                "category": target.category,
                "quantity": qty_per_order,
                "unit_price": round(target.price, 2),
                "line_total": round(target.price * qty_per_order, 2),
            }
        ]
        _publish(prod, _build_order(items))
        time.sleep(0.2)
        if (i + 1) % 10 == 0:
            print(f"  sent {i + 1}/{times}")
    prod.flush(10)
    print("drain complete")


# ---------------------------------------------------------------------------
# clear alerts
# ---------------------------------------------------------------------------

def cmd_clear_alerts() -> None:
    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    try:
        cur = conn.cursor()
        cur.execute("UPDATE alerts SET resolved = 1 WHERE resolved = 0")
        conn.commit()
        print(f"resolved {cur.rowcount} alerts")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# reset stock (helpful between demos)
# ---------------------------------------------------------------------------

def cmd_reset_stock() -> None:
    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    try:
        cur = conn.cursor()
        # Re-run seed by reading the SQL file
        seed_path = Path(__file__).resolve().parents[1] / "database" / "seed_products.sql"
        sql = seed_path.read_text()
        for stmt in [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]:
            if stmt.upper().startswith(("USE", "INSERT")):
                try:
                    cur.execute(stmt)
                except mysql.connector.Error as e:
                    print(f"skip: {e}")
        conn.commit()
        print("stock reset from seed_products.sql")
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("burst", help="Flash-sale burst to trigger REVENUE_SPIKE")
    b.add_argument("--size", type=int, default=60)
    b.add_argument("--duration", type=float, default=15.0)

    d = sub.add_parser("drain", help="Hammer one SKU to trigger LOW_STOCK")
    d.add_argument("--product", type=int, required=True)
    d.add_argument("--times", type=int, default=40)
    d.add_argument("--qty-per-order", type=int, default=3)

    sub.add_parser("clear-alerts", help="Mark all alerts resolved")
    sub.add_parser("reset-stock", help="Restore stock from seed file")

    args = parser.parse_args()
    if args.cmd == "burst":
        cmd_burst(args.size, args.duration)
    elif args.cmd == "drain":
        cmd_drain(args.product, args.times, args.qty_per_order)
    elif args.cmd == "clear-alerts":
        cmd_clear_alerts()
    elif args.cmd == "reset-stock":
        cmd_reset_stock()


if __name__ == "__main__":
    main()
