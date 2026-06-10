"""
Spark Structured Streaming consumer for the olist.orders topic.

Two modes:
  agg  (default) — event-time windowed order counts by status, to console.
  raw            — append parsed orders to a Parquet landing zone with a
                   checkpoint, so the stream is restartable exactly-once.

The Kafka connector jar is pulled via spark.jars.packages on first run
(needs internet once; Ivy caches it afterwards).

Run (broker up + producer replaying):
    python -m streaming.spark_consumer
    python -m streaming.spark_consumer --mode raw
"""
from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

from ingestion.config import settings

SCALA_VER = "2.12"
SPARK_VER = "3.5.3"
KAFKA_PKG = f"org.apache.spark:spark-sql-kafka-0-10_{SCALA_VER}:{SPARK_VER}"

# Raw orders arrive as JSON strings; everything is read as string then cast.
ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType()),
    StructField("customer_id", StringType()),
    StructField("order_status", StringType()),
    StructField("order_purchase_timestamp", StringType()),
    StructField("order_approved_at", StringType()),
    StructField("order_delivered_customer_date", StringType()),
    StructField("order_estimated_delivery_date", StringType()),
])

CHECKPOINT_DIR = settings.raw_dir.parent / "streaming" / "_checkpoints" / "orders"
PARQUET_SINK = settings.raw_dir.parent / "streaming" / "orders"


def _spark() -> SparkSession:
    return (
        SparkSession.builder.appName("olist-orders-consumer")
        .config("spark.jars.packages", KAFKA_PKG)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def _parsed(spark: SparkSession):
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", settings.kafka_bootstrap_servers)
        .option("subscribe", settings.kafka_topic_orders)
        .option("startingOffsets", "earliest")
        .load()
    )
    return (
        raw.select(F.from_json(F.col("value").cast("string"), ORDERS_SCHEMA).alias("o"))
        .select("o.*")
        .withColumn("purchased_at", F.to_timestamp("order_purchase_timestamp"))
    )


def run_agg(spark: SparkSession) -> None:
    parsed = _parsed(spark)
    windowed = (
        parsed.withWatermark("purchased_at", "2 days")
        .groupBy(F.window("purchased_at", "1 day").alias("w"), F.col("order_status"))
        .count()
        .select(
            F.col("w.start").alias("window_start"),
            F.col("order_status"),
            F.col("count").alias("n_orders"),
        )
    )
    query = (
        windowed.writeStream.outputMode("update")
        .format("console")
        .option("truncate", "false")
        .option("numRows", 20)
        .start()
    )
    query.awaitTermination()


def run_raw(spark: SparkSession) -> None:
    parsed = _parsed(spark)
    query = (
        parsed.writeStream.format("parquet")
        .option("path", str(PARQUET_SINK))
        .option("checkpointLocation", str(CHECKPOINT_DIR))
        .outputMode("append")
        .start()
    )
    query.awaitTermination()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="agg", choices=["agg", "raw"])
    args = ap.parse_args()

    spark = _spark()
    spark.sparkContext.setLogLevel("WARN")
    if args.mode == "agg":
        run_agg(spark)
    else:
        run_raw(spark)


if __name__ == "__main__":
    main()
