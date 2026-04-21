#!/usr/bin/env bash
# One-command launcher: brings up Kafka + MySQL, creates topics,
# then starts Spark, the generator, the anomaly detector, and the
# KPI evaluator in the background. Ctrl-C stops all background jobs.
set -e
cd "$(dirname "$0")/.."

PYTHON=".venv/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON=".venv/bin/python"

echo ">> starting docker stack"
docker compose -f docker/docker-compose.yml up -d

echo ">> waiting for Kafka..."
for _ in $(seq 1 30); do
    if docker exec ecom_kafka kafka-topics --bootstrap-server kafka:29092 --list >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo ">> creating topics"
bash scripts/create_topics.sh

echo ">> waiting for MySQL..."
for _ in $(seq 1 30); do
    if docker exec ecom_mysql mysqladmin ping -uroot -proot_pass --silent >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

mkdir -p logs

echo ">> launching Spark streaming job"
bash scripts/run_spark.sh > logs/spark.log 2>&1 &
SPARK_PID=$!

echo ">> giving Spark 20s to warm up..."
sleep 20

echo ">> starting order generator"
"$PYTHON" -m generator.order_producer > logs/generator.log 2>&1 &
GEN_PID=$!

echo ">> starting anomaly detector"
"$PYTHON" -m anomaly.detector > logs/anomaly.log 2>&1 &
ANO_PID=$!

echo ">> starting KPI evaluator"
"$PYTHON" -m kpi.evaluator > logs/kpi.log 2>&1 &
KPI_PID=$!

echo ""
echo "All components running. PIDs: spark=$SPARK_PID gen=$GEN_PID anomaly=$ANO_PID kpi=$KPI_PID"
echo "Logs in ./logs/. Ctrl-C to stop."
trap 'echo stopping...; kill $SPARK_PID $GEN_PID $ANO_PID $KPI_PID 2>/dev/null; exit 0' INT TERM
wait
