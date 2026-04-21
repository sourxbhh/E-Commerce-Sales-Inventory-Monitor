#!/usr/bin/env bash
# Create the two Kafka topics used by the pipeline.
set -e

docker exec ecom_kafka kafka-topics \
    --bootstrap-server kafka:29092 \
    --create --if-not-exists \
    --topic orders \
    --partitions 3 --replication-factor 1

docker exec ecom_kafka kafka-topics \
    --bootstrap-server kafka:29092 \
    --create --if-not-exists \
    --topic inventory-updates \
    --partitions 3 --replication-factor 1

echo "Topics ready:"
docker exec ecom_kafka kafka-topics --bootstrap-server kafka:29092 --list
