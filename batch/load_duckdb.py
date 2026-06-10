"""
Load the partitioned Parquet under data/processed/ into the DuckDB `raw` schema,
one table per Olist source. dbt then reads from raw.* (see warehouse/).

Each table is rebuilt with CREATE OR REPLACE, so the load is idempotent.
Partitioned tables (orders, order_reviews) are unioned across their year_month
partitions via a recursive glob + hive partitioning.

Run:
    python -m batch.load_duckdb
"""
from __future__ import annotations

import logging

import duckdb

from ingestion.config import settings

log = logging.getLogger("load_duckdb")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s")

# Olist source tables, mirroring ingestion/olist_to_parquet.py's out_name set.
TABLES: tuple[str, ...] = (
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "customers",
    "products",
    "sellers",
    "geolocation",
    "product_category_name_translation",
)


def load() -> None:
    if not settings.processed_dir.exists():
        raise SystemExit(
            f"{settings.processed_dir} does not exist — run "
            f"`python -m ingestion.olist_to_parquet` first"
        )

    settings.duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(settings.duckdb_path))
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.warehouse_schema_raw}")

    total_rows = 0
    for table in TABLES:
        src_dir = settings.processed_dir / table
        if not src_dir.exists():
            log.warning("skip %s (missing %s)", table, src_dir)
            continue

        glob = (src_dir / "**" / "*.parquet").as_posix()
        fq = f"{settings.warehouse_schema_raw}.{table}"
        con.execute(
            f"CREATE OR REPLACE TABLE {fq} AS "
            f"SELECT * FROM read_parquet(?, hive_partitioning => true, union_by_name => true)",
            [glob],
        )
        n = con.execute(f"SELECT count(*) FROM {fq}").fetchone()[0]
        total_rows += n
        log.info("loaded %s rows -> %s", f"{n:,}", fq)

    con.close()
    log.info(
        "done. %s rows across %d tables -> %s",
        f"{total_rows:,}",
        len(TABLES),
        settings.duckdb_path,
    )


if __name__ == "__main__":
    load()
