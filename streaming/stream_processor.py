"""
Spark Structured Streaming pipeline.

Reads orders from Kafka, decrements inventory, aggregates minute-level
revenue + per-product sales, and writes everything to MySQL via JDBC
inside a foreachBatch sink. Low-stock products trigger alert rows.

Run (from project root):
    spark-submit --packages \
      org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,\
      mysql:mysql-connector-java:8.0.33 \
      streaming/stream_processor.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    ArrayType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
    DecimalType,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.config import KAFKA, MYSQL  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] stream_processor: %(message)s",
)
log = logging.getLogger("stream_processor")


ORDER_SCHEMA = StructType(
    [
        StructField("order_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("order_timestamp", TimestampType(), False),
        StructField("total_amount", DecimalType(12, 2), False),
        StructField("item_count", IntegerType(), False),
        StructField("status", StringType(), True),
        StructField(
            "items",
            ArrayType(
                StructType(
                    [
                        StructField("product_id", IntegerType(), False),
                        StructField("product_name", StringType(), True),
                        StructField("category", StringType(), True),
                        StructField("quantity", IntegerType(), False),
                        StructField("unit_price", DecimalType(10, 2), False),
                        StructField("line_total", DecimalType(12, 2), True),
                    ]
                )
            ),
            False,
        ),
    ]
)


JDBC_PROPS = {
    "user": MYSQL.user,
    "password": MYSQL.password,
    "driver": "com.mysql.cj.jdbc.Driver",
}


def build_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("ecom-realtime-monitor")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.streaming.checkpointLocation", "./checkpoints/main")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def read_orders(spark: SparkSession) -> DataFrame:
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA.bootstrap_servers)
        .option("subscribe", KAFKA.orders_topic)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed = (
        raw.selectExpr("CAST(value AS STRING) AS json_str", "timestamp AS kafka_ts")
        .withColumn("payload", F.from_json("json_str", ORDER_SCHEMA))
        .select("payload.*", "kafka_ts")
        .withWatermark("order_timestamp", "10 minutes")
    )
    return parsed


# ---------------------------------------------------------------------------
# JDBC writers (run inside foreachBatch)
# ---------------------------------------------------------------------------

def _write_jdbc(df: DataFrame, table: str, mode: str = "append") -> None:
    (
        df.write.format("jdbc")
        .option("url", MYSQL.jdbc_url)
        .option("dbtable", table)
        .option("user", JDBC_PROPS["user"])
        .option("password", JDBC_PROPS["password"])
        .option("driver", JDBC_PROPS["driver"])
        .option("batchsize", 500)
        .mode(mode)
        .save()
    )


def _upsert_via_staging(
    df: DataFrame,
    target_table: str,
    upsert_sql: str,
    staging_table: str,
) -> None:
    """Spark JDBC has no native upsert, so stage then MERGE via raw SQL."""
    if df.rdd.isEmpty():
        return
    _write_jdbc(df, staging_table, mode="overwrite")

    import mysql.connector  # local import keeps driver load off executors

    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    try:
        cur = conn.cursor()
        cur.execute(upsert_sql)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# foreachBatch sink
# ---------------------------------------------------------------------------

def process_batch(batch_df: DataFrame, batch_id: int) -> None:
    if batch_df.rdd.isEmpty():
        return

    batch_df.persist()
    log.info("[batch %d] received %d orders", batch_id, batch_df.count())

    # 1. Append raw orders
    orders_out = batch_df.select(
        "order_id",
        "customer_id",
        "order_timestamp",
        "total_amount",
        "item_count",
        F.coalesce(F.col("status"), F.lit("CREATED")).alias("status"),
    )
    _write_jdbc(orders_out, "orders", mode="append")

    # 2. Explode items -> order_items
    items = batch_df.select(
        "order_id",
        F.explode("items").alias("item"),
    ).select(
        "order_id",
        F.col("item.product_id").alias("product_id"),
        F.col("item.quantity").alias("quantity"),
        F.col("item.unit_price").alias("unit_price"),
    )
    items.persist()
    _write_jdbc(items, "order_items", mode="append")

    # 3. Minute-level sales_metrics (tumbling 1-min window)
    revenue_minute = (
        batch_df.groupBy(F.window("order_timestamp", "1 minute").alias("w"))
        .agg(
            F.sum("total_amount").alias("revenue"),
            F.count("*").alias("order_count"),
            F.sum("item_count").alias("item_count"),
        )
        .select(
            F.col("w.start").alias("window_start"),
            F.col("w.end").alias("window_end"),
            F.col("revenue"),
            F.col("order_count"),
            F.col("item_count"),
            (F.col("revenue") / F.col("order_count")).cast(DecimalType(10, 2)).alias("avg_order_value"),
        )
    )
    _upsert_via_staging(
        revenue_minute,
        target_table="sales_metrics",
        staging_table="_stg_sales_metrics",
        upsert_sql=(
            "INSERT INTO sales_metrics "
            "(window_start, window_end, revenue, order_count, item_count, avg_order_value) "
            "SELECT window_start, window_end, revenue, order_count, item_count, avg_order_value "
            "FROM _stg_sales_metrics "
            "ON DUPLICATE KEY UPDATE "
            "revenue = sales_metrics.revenue + VALUES(revenue), "
            "order_count = sales_metrics.order_count + VALUES(order_count), "
            "item_count = sales_metrics.item_count + VALUES(item_count), "
            "avg_order_value = "
            "((sales_metrics.revenue + VALUES(revenue)) / "
            " (sales_metrics.order_count + VALUES(order_count)));"
        ),
    )

    # 4. Per-product minute aggregates
    product_minute = (
        batch_df.select(
            F.col("order_timestamp"),
            F.explode("items").alias("item"),
        )
        .groupBy(
            F.window("order_timestamp", "1 minute").alias("w"),
            F.col("item.product_id").alias("product_id"),
        )
        .agg(
            F.sum("item.quantity").alias("units_sold"),
            F.sum(F.col("item.unit_price") * F.col("item.quantity")).alias("revenue"),
        )
        .select(
            F.col("w.start").alias("window_start"),
            F.col("w.end").alias("window_end"),
            "product_id",
            "units_sold",
            F.col("revenue").cast(DecimalType(12, 2)).alias("revenue"),
        )
    )
    _upsert_via_staging(
        product_minute,
        target_table="product_sales_metrics",
        staging_table="_stg_product_sales_metrics",
        upsert_sql=(
            "INSERT INTO product_sales_metrics "
            "(window_start, window_end, product_id, units_sold, revenue) "
            "SELECT window_start, window_end, product_id, units_sold, revenue "
            "FROM _stg_product_sales_metrics "
            "ON DUPLICATE KEY UPDATE "
            "units_sold = product_sales_metrics.units_sold + VALUES(units_sold), "
            "revenue = product_sales_metrics.revenue + VALUES(revenue);"
        ),
    )

    # 5. Inventory decrement + low-stock alerts (raw SQL via connector)
    decrements = (
        items.groupBy("product_id")
        .agg(F.sum("quantity").alias("qty"))
        .collect()
    )
    if decrements:
        import mysql.connector

        conn = mysql.connector.connect(
            host=MYSQL.host,
            port=MYSQL.port,
            user=MYSQL.user,
            password=MYSQL.password,
            database=MYSQL.database,
        )
        try:
            cur = conn.cursor()
            for row in decrements:
                pid, qty = int(row["product_id"]), int(row["qty"])
                cur.execute(
                    "UPDATE products SET stock_quantity = GREATEST(0, stock_quantity - %s) "
                    "WHERE product_id = %s",
                    (qty, pid),
                )
                cur.execute(
                    "SELECT stock_quantity FROM products WHERE product_id = %s",
                    (pid,),
                )
                stock_after = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO inventory_log "
                    "(product_id, change_type, quantity_change, stock_after) "
                    "VALUES (%s, 'SALE', %s, %s)",
                    (pid, -qty, stock_after),
                )

            # Low-stock alert insert (guard duplicates within 10 minutes)
            cur.execute(
                """
                INSERT INTO alerts
                    (alert_type, severity, entity_type, entity_id, message,
                     detected_value, expected_low, expected_high)
                SELECT 'LOW_STOCK',
                       CASE WHEN p.stock_quantity = 0 THEN 'CRITICAL'
                            WHEN p.stock_quantity <= p.reorder_threshold / 2 THEN 'HIGH'
                            ELSE 'WARNING' END,
                       'PRODUCT', CAST(p.product_id AS CHAR),
                       CONCAT('Low stock: ', p.name,
                              ' (', p.stock_quantity, ' <= ', p.reorder_threshold, ')'),
                       p.stock_quantity, 0, p.reorder_threshold
                FROM products p
                WHERE p.stock_quantity <= p.reorder_threshold
                  AND NOT EXISTS (
                      SELECT 1 FROM alerts a
                      WHERE a.alert_type = 'LOW_STOCK'
                        AND a.entity_id = CAST(p.product_id AS CHAR)
                        AND a.detected_at > (NOW() - INTERVAL 10 MINUTE)
                  );
                """
            )
            conn.commit()
        finally:
            conn.close()

    items.unpersist()
    batch_df.unpersist()


def main() -> None:
    os.makedirs("checkpoints/main", exist_ok=True)
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")

    orders = read_orders(spark)

    query = (
        orders.writeStream.foreachBatch(process_batch)
        .outputMode("append")
        .trigger(processingTime="10 seconds")
        .start()
    )

    log.info("Streaming query started. Awaiting termination...")
    query.awaitTermination()


if __name__ == "__main__":
    main()
