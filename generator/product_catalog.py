"""Loads the product catalog from MySQL for the generator to draw from."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

import mysql.connector

from generator.config import MYSQL

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Product:
    product_id: int
    name: str
    category: str
    price: float
    popularity_weight: float


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
            "SELECT product_id, name, category, price, popularity_weight "
            "FROM products"
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
    log.info("Loaded %d products from MySQL", len(products))
    return products
