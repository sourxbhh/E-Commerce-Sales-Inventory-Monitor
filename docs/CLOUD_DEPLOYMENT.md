# Cloud deployment (optional polish)

Migrating the stack onto managed services kills the "localhost MySQL
+ laptop Docker" fragility and makes it a real talking point on a
resume. Three realistic paths:

## Path A — GCP (aligns with the original guide)

| Local component | Cloud replacement | Notes |
|---|---|---|
| Kafka + Zookeeper | **Pub/Sub** topic + subscription | Or use **Confluent Cloud** Kafka to keep the same producer code. |
| Spark Structured Streaming | **Dataflow** (Apache Beam) or **Dataproc** | Dataflow is the GCP-native pick; Dataproc keeps the Spark code unchanged. |
| MySQL | **Cloud SQL for MySQL** | Minimal code change (connection string only). |
| Python workers | **Cloud Run Jobs** (scheduled) or **Compute Engine** | Run anomaly + KPI on a schedule; no always-on cost. |
| Power BI DirectQuery | Same — use a **Power BI Gateway** on a small GCE VM, OR migrate to **Looker Studio** for a zero-gateway alternative. |

### Minimum viable GCP deployment

1. Provision Cloud SQL MySQL, apply `schema.sql` + `seed_products.sql`.
2. Create a Pub/Sub topic `orders`; keep topic name configurable via
   `.env` so the producer only changes broker/URL.
3. Drop the generator onto Cloud Run as a scheduled job (Cloud Scheduler every minute, burst mode triggered by a second scheduled job).
4. Deploy the Spark job to Dataproc with the same JARs:
   ```
   gcloud dataproc jobs submit pyspark streaming/stream_processor.py \
     --cluster ecom-cluster \
     --properties spark.jars.packages=org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,com.mysql:mysql-connector-j:8.4.0
   ```
5. Deploy `detector.py` and `evaluator.py` as Cloud Run Jobs on a
   1-minute Cloud Scheduler trigger.
6. Power BI: install the gateway on a small GCE VM inside the same
   VPC as Cloud SQL; the `.pbix` connection string swaps `localhost`
   for the private IP.

## Path B — BigQuery-native (cheaper, more analytical)

Swap MySQL + Spark entirely for streaming inserts to BigQuery:

- Producer → Pub/Sub.
- Pub/Sub → BigQuery subscription (no Dataflow needed for simple
  inserts).
- BigQuery materialised views compute the minute aggregates on the fly.
- Anomaly detector queries BigQuery instead of MySQL.
- Power BI uses the native BigQuery connector (DirectQuery supported).

Trade-off: loses exactly-once windowed aggregation semantics, but
gains a pure-SQL analytical layer — a stronger fit if you want to
lean into the BI-Analyst angle.

## Path C — Railway + Neon (cheapest, fits "side-project" scope)

If the goal is just a public demo URL:

- **Railway**: deploy generator + detector + evaluator as three small
  services.
- **Neon** (serverless Postgres) or **Railway MySQL**: managed DB.
- **Confluent Cloud**: free-tier Kafka.
- Skip Spark entirely for this tier — replace with a 50-line Python
  consumer that does the same per-minute aggregation (acceptable
  compromise given the scale).
- Power BI is desktop-only; alternatively swap for a small Streamlit
  app or a Looker Studio report pointed at the DB.

## Config parity

All three paths work with the existing `.env` — the producer,
detector, and KPI evaluator only need the right connection strings.
The Spark job is the one piece that would change meaningfully if you
move off Spark (Path B/C).

## Security checklist before publishing anywhere

- Rotate the `ecom_user` password; never commit real creds.
- Use IAM auth for Cloud SQL (skip password entirely on GCP).
- Put the Spark cluster and MySQL in the same VPC; don't expose
  3306 publicly.
- Scrub `customer_id` values — they're `CUST-#####` fakes today, but
  enforce that contract before onboarding any real data.
