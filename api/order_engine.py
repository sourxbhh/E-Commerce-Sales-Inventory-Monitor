"""
Synthesizes orders against the real FakeStoreAPI catalog.

Basket realism comes from two places:
  * product popularity is weighted by rating.count (synced into
    products.popularity_weight by fakestore_sync).
  * basket size + per-line quantity distributions are mined from
    the real /carts endpoint on startup.
"""
from __future__ import annotations

import logging
import random
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import mysql.connector

from fakestore.client import fetch_carts
from generator.config import MYSQL

log = logging.getLogger("order_engine")


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    category: str
    price: float
    popularity_weight: float


@dataclass(frozen=True)
class BasketStats:
    size_dist: List[int]      # sample-able list of realistic basket sizes
    quantity_dist: List[int]  # sample-able list of realistic quantities

    @classmethod
    def default(cls) -> "BasketStats":
        # reasonable defaults before we've pulled /carts
        return cls(
            size_dist=[1] * 30 + [2] * 35 + [3] * 20 + [4] * 10 + [5] * 5,
            quantity_dist=[1] * 70 + [2] * 20 + [3] * 7 + [4] * 2 + [5] * 1,
        )


def load_products() -> List[Product]:
    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT product_id, name, category, price, popularity_weight
            FROM products
            WHERE source = 'fakestoreapi'
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    products = [
        Product(
            product_id=r["product_id"],
            name=r["name"],
            category=r["category"],
            price=float(r["price"]),
            popularity_weight=float(r["popularity_weight"]),
        )
        for r in rows
    ]
    log.info("loaded %d products from MySQL (source=fakestoreapi)", len(products))
    return products


async def mine_basket_stats() -> BasketStats:
    """
    Pull /carts once and turn the real basket distribution into sampleable
    lists. Falls back to sensible defaults if the call fails.
    """
    try:
        carts = await fetch_carts()
    except Exception as e:  # noqa: BLE001
        log.warning("could not fetch /carts (%s); using default basket stats", e)
        return BasketStats.default()

    size_counter: Counter = Counter()
    qty_counter: Counter = Counter()
    for cart in carts:
        items = cart.get("products", [])
        size_counter[min(len(items), 8)] += 1
        for item in items:
            q = min(int(item.get("quantity", 1)), 8)
            qty_counter[q] += 1

    # expand into sample-able lists weighted by frequency
    size_dist = [k for k, v in size_counter.items() for _ in range(v)]
    qty_dist = [k for k, v in qty_counter.items() for _ in range(v)]
    if not size_dist:
        size_dist = BasketStats.default().size_dist
    if not qty_dist:
        qty_dist = BasketStats.default().quantity_dist

    log.info(
        "mined basket stats from %d carts: size_dist=%s quantity_dist=%s",
        len(carts),
        dict(size_counter),
        dict(qty_counter),
    )
    return BasketStats(size_dist=size_dist, quantity_dist=qty_dist)


def build_order(
    products: List[Product],
    basket: BasketStats,
    forced_product_ids: Optional[List[int]] = None,
) -> dict:
    """Produce one order dict matching the Kafka schema."""
    if forced_product_ids:
        picked = [p for p in products if p.product_id in forced_product_ids]
        if not picked:
            picked = random.sample(products, k=min(2, len(products)))
    else:
        size = random.choice(basket.size_dist)
        weights = [p.popularity_weight for p in products]
        picked = random.choices(products, weights=weights, k=size)

    items = []
    total = 0.0
    for prod in picked:
        qty = random.choice(basket.quantity_dist)
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
        "order_id": str(uuid.uuid4()),
        "customer_id": f"CUST-{random.randint(1, 5000):05d}",
        "order_timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "total_amount": round(total, 2),
        "item_count": sum(it["quantity"] for it in items),
        "items": items,
        "status": "CREATED",
    }
