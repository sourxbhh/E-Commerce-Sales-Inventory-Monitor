"""
Great Expectations validation of the DuckDB `raw` schema.

Each table is pulled into pandas and checked against a small suite of
expectations (keys not-null/unique, categoricals in range, money non-negative).
Exits non-zero if any suite fails, so an orchestrator (Airflow) can gate on it.

Run:
    python -m quality.validate
"""
from __future__ import annotations

import logging

import duckdb
import great_expectations as gx
import great_expectations.expectations as gxe

from ingestion.config import settings

log = logging.getLogger("ge_validate")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s")

ORDER_STATUSES = [
    "delivered", "shipped", "canceled", "unavailable",
    "invoiced", "processing", "created", "approved",
]

# table -> list of expectations to apply
SUITES: dict[str, list] = {
    "orders": [
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToBeUnique(column="order_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gxe.ExpectColumnValuesToBeInSet(column="order_status", value_set=ORDER_STATUSES),
    ],
    "order_items": [
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="product_id"),
        gxe.ExpectColumnValuesToBeBetween(column="price", min_value=0),
        gxe.ExpectColumnValuesToBeBetween(column="freight_value", min_value=0),
    ],
    "order_payments": [
        gxe.ExpectColumnValuesToNotBeNull(column="order_id"),
        gxe.ExpectColumnValuesToBeBetween(column="payment_value", min_value=0),
    ],
    "order_reviews": [
        gxe.ExpectColumnValuesToNotBeNull(column="review_id"),
        gxe.ExpectColumnValuesToBeBetween(column="review_score", min_value=1, max_value=5),
    ],
    "customers": [
        gxe.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gxe.ExpectColumnValuesToBeUnique(column="customer_id"),
    ],
    "products": [
        gxe.ExpectColumnValuesToBeUnique(column="product_id"),
    ],
}


def validate() -> bool:
    con = duckdb.connect(str(settings.duckdb_path), read_only=True)
    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_pandas(name="olist_raw")

    all_ok = True
    for table, expectations in SUITES.items():
        df = con.execute(
            f"SELECT * FROM {settings.warehouse_schema_raw}.{table}"
        ).fetch_df()

        asset = datasource.add_dataframe_asset(name=table)
        batch_def = asset.add_batch_definition_whole_dataframe(f"{table}_batch")
        suite = context.suites.add(gx.ExpectationSuite(name=f"{table}_suite"))
        for exp in expectations:
            suite.add_expectation(exp)

        validation_def = context.validation_definitions.add(
            gx.ValidationDefinition(name=f"{table}_vd", data=batch_def, suite=suite)
        )
        result = validation_def.run(batch_parameters={"dataframe": df})

        n_total = len(result.results)
        n_passed = sum(1 for r in result.results if r.success)
        status = "PASS" if result.success else "FAIL"
        log.info("%-18s %s (%d/%d expectations, %s rows)",
                 table, status, n_passed, n_total, f"{len(df):,}")
        if not result.success:
            all_ok = False
            for r in result.results:
                if not r.success:
                    cfg = r.expectation_config
                    log.warning("  ✗ %s %s", cfg.type, cfg.kwargs)

    con.close()
    log.info("overall: %s", "PASS" if all_ok else "FAIL")
    return all_ok


def main() -> None:
    if not validate():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
