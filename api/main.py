"""
FastAPI live-edge service for the realtime e-commerce monitor.

Responsibilities:
  * Loads the real product catalog (FakeStoreAPI -> MySQL).
  * Background task: generates orders at a configurable rate and
    publishes them to Kafka (so Spark Streaming picks them up).
  * Fans the same orders out to WebSocket subscribers so a web
    dashboard or notebook can tap the live stream with zero Kafka
    setup on the client side.
  * HTTP endpoints for catalog inspection, stats, and on-demand
    demo triggers (burst, drain).

Run:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
or via the orchestrator (python scripts/orchestrator.py up).
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Set

from confluent_kafka import Producer
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from api.order_engine import (
    BasketStats,
    Product,
    build_order,
    load_products,
    mine_basket_stats,
)
from generator.config import API, BURST, KAFKA

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] api: %(message)s",
)
log = logging.getLogger("api")


# ---------------------------------------------------------------------------
# shared state carried on the app
# ---------------------------------------------------------------------------

class AppState:
    products: List[Product] = []
    basket: BasketStats = BasketStats.default()
    producer: Producer | None = None
    subscribers: Set["asyncio.Queue[dict]"] = set()
    orders_sent: int = 0
    started_at: float = time.time()
    last_burst_at: float = 0.0
    burst_pending: int = 0       # demo-controller knob
    drain_product_id: int | None = None
    drain_remaining: int = 0


STATE = AppState()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _build_producer() -> Producer:
    return Producer(
        {
            "bootstrap.servers": KAFKA.bootstrap_servers,
            "client.id": "api-order-producer",
            "linger.ms": 20,
            "acks": "all",
        }
    )


def _delivery_report(err, msg):  # noqa: ARG001
    if err is not None:
        log.error("kafka delivery failed: %s", err)


async def _broadcast(order: dict) -> None:
    dead: List["asyncio.Queue[dict]"] = []
    for q in list(STATE.subscribers):
        try:
            q.put_nowait(order)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        STATE.subscribers.discard(q)


def _publish(order: dict) -> None:
    if STATE.producer is None:
        return
    STATE.producer.produce(
        topic=KAFKA.orders_topic,
        key=order["order_id"].encode(),
        value=json.dumps(order).encode(),
        callback=_delivery_report,
    )
    STATE.producer.poll(0)


async def _emit(order: dict) -> None:
    _publish(order)
    await _broadcast(order)
    STATE.orders_sent += 1


# ---------------------------------------------------------------------------
# background generator loop
# ---------------------------------------------------------------------------

async def order_generator_loop() -> None:
    """Produces one order every API.order_min..order_max seconds, plus bursts."""
    log.info(
        "generator loop starting: %d products, rate=%.1f-%.1fs, burst=%s",
        len(STATE.products), API.order_min, API.order_max, BURST.enabled,
    )
    while True:
        try:
            # scheduled burst?
            due_burst = (
                BURST.enabled
                and time.time() - STATE.last_burst_at >= BURST.every_seconds
            )
            if due_burst or STATE.burst_pending > 0:
                size = STATE.burst_pending or BURST.size
                STATE.burst_pending = 0
                duration = BURST.duration if due_burst else max(5, size // 4)
                log.warning("BURST: %d orders over %ds", size, duration)
                delay = duration / max(size, 1)
                for _ in range(size):
                    order = build_order(STATE.products, STATE.basket)
                    await _emit(order)
                    await asyncio.sleep(delay)
                STATE.last_burst_at = time.time()
                continue

            # drain mode? (demo controller: hammer one SKU)
            if STATE.drain_remaining > 0 and STATE.drain_product_id:
                order = build_order(
                    STATE.products,
                    STATE.basket,
                    forced_product_ids=[STATE.drain_product_id],
                )
                await _emit(order)
                STATE.drain_remaining -= 1
                if STATE.drain_remaining == 0:
                    log.info("drain complete (product %s)", STATE.drain_product_id)
                    STATE.drain_product_id = None
                await asyncio.sleep(0.3)
                continue

            # normal cadence
            order = build_order(STATE.products, STATE.basket)
            await _emit(order)
            if STATE.orders_sent % 10 == 0:
                log.info("orders_sent=%d subscribers=%d",
                         STATE.orders_sent, len(STATE.subscribers))
            await asyncio.sleep(random.uniform(API.order_min, API.order_max))
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            log.exception("generator iteration failed; sleeping before retry")
            await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    log.info("bootstrapping live-edge service")
    STATE.products = load_products()
    if not STATE.products:
        log.error("no products in MySQL; run scripts/fakestore_sync.py first")
    STATE.basket = await mine_basket_stats()
    STATE.producer = _build_producer()
    task = asyncio.create_task(order_generator_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        if STATE.producer:
            STATE.producer.flush(10)
        log.info("shutdown complete")


app = FastAPI(title="E-commerce Live Edge", version="1.0.0", lifespan=lifespan)


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "products": len(STATE.products),
        "subscribers": len(STATE.subscribers),
        "orders_sent": STATE.orders_sent,
        "uptime_seconds": int(time.time() - STATE.started_at),
    }


@app.get("/products")
async def list_products() -> List[dict]:
    return [
        {
            "product_id": p.product_id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "popularity_weight": p.popularity_weight,
        }
        for p in STATE.products
    ]


@app.get("/products/{product_id}")
async def get_product(product_id: int) -> dict:
    for p in STATE.products:
        if p.product_id == product_id:
            return {
                "product_id": p.product_id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "popularity_weight": p.popularity_weight,
            }
    raise HTTPException(status_code=404, detail="product not found")


@app.get("/stats")
async def stats() -> dict:
    return {
        "orders_sent": STATE.orders_sent,
        "uptime_seconds": int(time.time() - STATE.started_at),
        "rate_per_minute": round(
            STATE.orders_sent / max((time.time() - STATE.started_at) / 60, 1), 2
        ),
        "subscribers": len(STATE.subscribers),
        "last_burst_seconds_ago": (
            int(time.time() - STATE.last_burst_at) if STATE.last_burst_at else None
        ),
        "drain_active": STATE.drain_remaining > 0,
        "drain_remaining": STATE.drain_remaining,
    }


@app.post("/trigger/burst")
async def trigger_burst(size: int = 40) -> Dict[str, object]:
    if size < 1 or size > 500:
        raise HTTPException(status_code=400, detail="size must be 1..500")
    STATE.burst_pending = size
    return {"queued": True, "size": size}


@app.post("/trigger/drain")
async def trigger_drain(product_id: int, times: int = 30) -> Dict[str, object]:
    if not any(p.product_id == product_id for p in STATE.products):
        raise HTTPException(status_code=404, detail="product not found")
    if times < 1 or times > 500:
        raise HTTPException(status_code=400, detail="times must be 1..500")
    STATE.drain_product_id = product_id
    STATE.drain_remaining = times
    return {"queued": True, "product_id": product_id, "times": times}


# ---------------------------------------------------------------------------
# WebSocket stream
# ---------------------------------------------------------------------------

@app.websocket("/stream/orders")
async def stream_orders(ws: WebSocket) -> None:
    await ws.accept()
    queue: "asyncio.Queue[dict]" = asyncio.Queue(maxsize=100)
    STATE.subscribers.add(queue)
    log.info("WS subscriber connected (total=%d)", len(STATE.subscribers))
    try:
        while True:
            order = await queue.get()
            await ws.send_json(order)
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        log.exception("WS subscriber error")
    finally:
        STATE.subscribers.discard(queue)
        log.info("WS subscriber removed (total=%d)", len(STATE.subscribers))
