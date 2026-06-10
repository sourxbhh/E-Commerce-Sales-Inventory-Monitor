"""
Convert the nine Olist CSVs in data/raw/ to partitioned / typed Parquet under
data/processed/. Orders + reviews are partitioned by year_month of their
respective timestamp columns; everything else is written as a single Parquet
file (these tables are small enough not to need partitioning).

Run:
    python -m ingestion.olist_to_parquet
"""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from ingestion.config import settings

log = logging.getLogger("olist_to_parquet")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s")


@dataclass(frozen=True)
class TableSpec:
    """One Olist source table → one parquet dataset."""

    csv_name: str
    out_name: str
    partition_ts_col: str | None = None  # column to derive year_month partitions from


TABLES: tuple[TableSpec, ...] = (
    TableSpec("olist_orders_dataset.csv", "orders", "order_purchase_timestamp"),
    TableSpec("olist_order_items_dataset.csv", "order_items"),
    TableSpec("olist_order_payments_dataset.csv", "order_payments"),
    TableSpec("olist_order_reviews_dataset.csv", "order_reviews", "review_creation_date"),
    TableSpec("olist_customers_dataset.csv", "customers"),
    TableSpec("olist_products_dataset.csv", "products"),
    TableSpec("olist_sellers_dataset.csv", "sellers"),
    TableSpec("olist_geolocation_dataset.csv", "geolocation"),
    TableSpec("product_category_name_translation.csv", "product_category_name_translation"),
)


def _read_csv(path: Path) -> pa.Table:
    """Read with PyArrow; let it infer types but coerce empty strings to nulls."""
    return pacsv.read_csv(
        path,
        convert_options=pacsv.ConvertOptions(strings_can_be_null=True),
        parse_options=pacsv.ParseOptions(newlines_in_values=True),
    )


def _add_year_month(table: pa.Table, ts_col: str) -> pa.Table:
    """Append a `year_month` STRING column (YYYY-MM) derived from `ts_col`."""
    ts = table[ts_col]
    # Some Olist timestamps are pure dates ("2017-10-02"); cast handles both.
    if not pa.types.is_timestamp(ts.type) and not pa.types.is_date(ts.type):
        ts = pc.strptime(ts, format="%Y-%m-%d %H:%M:%S", unit="s")
    year = pc.cast(pc.year(ts), pa.string())
    month = pc.cast(pc.month(ts), pa.string())
    # zero-pad month
    month = pc.binary_join_element_wise("0", month, "")
    month = pc.utf8_slice_codeunits(month, -2)
    year_month = pc.binary_join_element_wise(year, month, "-")
    return table.append_column("year_month", year_month)


def _convert(spec: TableSpec) -> None:
    src = settings.raw_dir / spec.csv_name
    dst = settings.processed_dir / spec.out_name

    if not src.exists():
        log.warning("skip %s (missing source %s)", spec.out_name, src.name)
        return

    log.info("reading %s", src.name)
    table = _read_csv(src)

    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    if spec.partition_ts_col:
        table = _add_year_month(table, spec.partition_ts_col)
        pq.write_to_dataset(
            table,
            root_path=str(dst),
            partition_cols=["year_month"],
            compression="snappy",
            existing_data_behavior="overwrite_or_ignore",
        )
        n_parts = len(list(dst.glob("year_month=*")))
        log.info("wrote %s rows to %s (%d partitions)", f"{table.num_rows:,}", dst.name, n_parts)
    else:
        pq.write_table(table, dst / "part-0.parquet", compression="snappy")
        log.info("wrote %s rows to %s", f"{table.num_rows:,}", dst.name)


def main() -> None:
    if not settings.raw_dir.exists():
        raise SystemExit(f"raw dir {settings.raw_dir} does not exist — see data/README.md")
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    for spec in TABLES:
        _convert(spec)
    log.info("done. processed/ -> %s", settings.processed_dir)


if __name__ == "__main__":
    main()
