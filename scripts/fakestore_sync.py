"""
Hydrate the `products` table from fakestoreapi.com.

Synthesized fields (FakeStoreAPI doesn't expose these):
  * stock_quantity    derived from rating.count (popular -> more stock)
  * reorder_threshold 20% of stock, floored at 10
  * popularity_weight log-scaled rating.count so heavy rating products
                      appear more often in generated orders.

Idempotent upsert -- re-running will refresh prices/ratings without
duplicating rows. Pass --reset to truncate downstream tables (orders,
alerts, metrics) for a clean demo.

Usage:
    python scripts/fakestore_sync.py          # normal refresh
    python scripts/fakestore_sync.py --reset  # wipe facts + re-seed
"""
from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fakestore.client import fetch_products_sync  # noqa: E402
from generator.config import MYSQL  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] fakestore_sync: %(message)s",
)
log = logging.getLogger("fakestore_sync")


def _synthesize_stock(rating_count: int) -> tuple[int, int, float]:
    """
    Turn rating.count into (stock, reorder_threshold, popularity_weight).
    More ratings => more popular => higher stock AND higher pick weight.
    """
    # stock between 80 and 600, scaling with sqrt(rating_count)
    rc = max(rating_count, 1)
    stock = int(80 + math.sqrt(rc) * 12)
    stock = min(stock, 600)
    reorder = max(int(stock * 0.2), 10)
    # popularity weight 1.0 .. 5.0 based on log(rating_count)
    weight = 1.0 + min(math.log10(rc + 1), 3.5)
    return stock, reorder, round(weight, 2)


def _apply_migration(cur) -> None:
    """Idempotent ALTER TABLE so existing installs pick up new columns."""
    migration_path = (
        Path(__file__).resolve().parents[1]
        / "database"
        / "migrations"
        / "001_fakestore_columns.sql"
    )
    sql = migration_path.read_text()
    for stmt in [s.strip() for s in sql.split(";") if s.strip()
                 and not s.strip().startswith("--")
                 and not s.strip().upper().startswith("USE")]:
        try:
            cur.execute(stmt)
        except mysql.connector.Error as e:
            # ADD COLUMN IF NOT EXISTS is MySQL 8.0.29+; older versions
            # raise on redundant statements which we can ignore.
            log.debug("migration step skipped: %s", e)


def upsert_products(reset: bool) -> int:
    log.info("fetching products from FakeStoreAPI...")
    products = fetch_products_sync()
    if not products:
        log.error("no products returned; aborting")
        return 0
    log.info("got %d products", len(products))

    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    try:
        cur = conn.cursor()
        _apply_migration(cur)

        if reset:
            log.warning("--reset: truncating downstream facts")
            cur.execute("SET FOREIGN_KEY_CHECKS=0")
            for table in (
                "alerts",
                "inventory_log",
                "order_items",
                "orders",
                "product_sales_metrics",
                "sales_metrics",
                "products",
            ):
                cur.execute(f"TRUNCATE TABLE {table}")
            cur.execute("SET FOREIGN_KEY_CHECKS=1")

        rows = []
        for p in products:
            pid = int(p["id"])
            name = p["title"][:490]
            category = p["category"][:78]
            price = float(p["price"])
            rc = int(p.get("rating", {}).get("count", 0))
            rr = float(p.get("rating", {}).get("rate", 0.0))
            stock, reorder, weight = _synthesize_stock(rc)
            rows.append(
                (
                    pid, name, category, price, stock, reorder, weight,
                    "fakestoreapi",
                    p.get("image", "")[:495],
                    p.get("description", "")[:2000],
                    rr, rc,
                )
            )

        cur.executemany(
            """
            INSERT INTO products
                (product_id, name, category, price, stock_quantity,
                 reorder_threshold, popularity_weight, source,
                 image_url, description, rating_rate, rating_count)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                category = VALUES(category),
                price = VALUES(price),
                popularity_weight = VALUES(popularity_weight),
                image_url = VALUES(image_url),
                description = VALUES(description),
                rating_rate = VALUES(rating_rate),
                rating_count = VALUES(rating_count),
                -- stock only filled on insert, not overwritten on update
                stock_quantity = IF(products.stock_quantity IS NULL,
                                    VALUES(stock_quantity),
                                    products.stock_quantity),
                reorder_threshold = IF(products.reorder_threshold IS NULL,
                                       VALUES(reorder_threshold),
                                       products.reorder_threshold)
            """,
            rows,
        )
        conn.commit()
        log.info("upserted %d products", len(rows))
        return len(rows)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true",
        help="truncate orders/alerts/metrics before loading (demo reset)",
    )
    args = parser.parse_args()
    n = upsert_products(reset=args.reset)
    if n == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
