"""
Streams simulated e-commerce orders into Kafka.

Normal mode: one order every ORDER_INTERVAL_MIN-MAX seconds.
Burst mode: every BURST_EVERY_SECONDS, emits BURST_SIZE orders in
BURST_DURATION_SECONDS -- simulating flash sales / bot attacks so
the anomaly detector has something real to catch during demos.
"""
from __future__ import annotations

import json
import logging
import random
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import List

from confluent_kafka import Producer
from faker import Faker

from generator.config import GENERATOR, KAFKA
from generator.product_catalog import Product, load_products

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("order_producer")

_fake = Faker()
_shutdown = False


def _handle_signal(signum, frame):  # noqa: ARG001
    global _shutdown
    log.info("Signal %s received, shutting down gracefully", signum)
    _shutdown = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def _delivery_report(err, msg):
    if err is not None:
        log.error("Kafka delivery failed: %s", err)


def _build_producer() -> Producer:
    conf = {
        "bootstrap.servers": KAFKA.bootstrap_servers,
        "client.id": "order-producer",
        "linger.ms": 20,
        "acks": "all",
    }
    return Producer(conf)


def _weighted_pick(products: List[Product], k: int) -> List[Product]:
    weights = [p.popularity_weight for p in products]
    return random.choices(products, weights=weights, k=k)


def _build_order(products: List[Product]) -> dict:
    order_id = str(uuid.uuid4())
    customer_id = f"CUST-{random.randint(1, 5000):05d}"
    item_count = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
    picked = _weighted_pick(products, item_count)

    items = []
    total = 0.0
    for prod in picked:
        qty = random.choices([1, 2, 3], weights=[75, 20, 5])[0]
        line_total = round(prod.price * qty, 2)
        total += line_total
        items.append(
            {
                "product_id": prod.product_id,
                "product_name": prod.name,
                "category": prod.category,
                "quantity": qty,
                "unit_price": round(prod.price, 2),
                "line_total": line_total,
            }
        )

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "total_amount": round(total, 2),
        "item_count": sum(it["quantity"] for it in items),
        "items": items,
        "status": "CREATED",
    }


def _publish(producer: Producer, topic: str, order: dict) -> None:
    payload = json.dumps(order).encode("utf-8")
    producer.produce(
        topic=topic,
        key=order["order_id"].encode("utf-8"),
        value=payload,
        callback=_delivery_report,
    )
    producer.poll(0)


def _should_burst(last_burst_ts: float) -> bool:
    if not GENERATOR.burst_enabled:
        return False
    return (time.time() - last_burst_ts) >= GENERATOR.burst_every_seconds


def run() -> None:
    products = load_products()
    if not products:
        log.error("No products loaded; seed the DB first.")
        sys.exit(1)

    producer = _build_producer()
    log.info(
        "Producing to %s on %s (normal every %d-%ds, burst=%s)",
        KAFKA.orders_topic,
        KAFKA.bootstrap_servers,
        GENERATOR.interval_min,
        GENERATOR.interval_max,
        GENERATOR.burst_enabled,
    )

    last_burst = time.time()
    orders_sent = 0

    try:
        while not _shutdown:
            if _should_burst(last_burst):
                log.warning(
                    "BURST: emitting %d orders over %ds",
                    GENERATOR.burst_size,
                    GENERATOR.burst_duration,
                )
                delay = GENERATOR.burst_duration / max(GENERATOR.burst_size, 1)
                for _ in range(GENERATOR.burst_size):
                    if _shutdown:
                        break
                    order = _build_order(products)
                    _publish(producer, KAFKA.orders_topic, order)
                    orders_sent += 1
                    time.sleep(delay)
                last_burst = time.time()
                continue

            order = _build_order(products)
            _publish(producer, KAFKA.orders_topic, order)
            orders_sent += 1
            if orders_sent % 10 == 0:
                log.info("Sent %d orders (latest total=$%.2f)", orders_sent, order["total_amount"])
            time.sleep(random.uniform(GENERATOR.interval_min, GENERATOR.interval_max))
    finally:
        producer.flush(10)
        log.info("Producer flushed. Total orders sent: %d", orders_sent)


if __name__ == "__main__":
    run()
