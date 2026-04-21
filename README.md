# Real-Time E-Commerce Sales & Inventory Monitor

End-to-end streaming pipeline that simulates e-commerce order traffic,
processes it with Spark Structured Streaming, stores aggregates in MySQL,
flags anomalies and KPI breaches in real time, and surfaces everything
through a Power BI dashboard (DirectQuery, 1-minute page refresh).

```
Python generator ─▶ Kafka ─▶ Spark Structured Streaming ─▶ MySQL ─▶ Power BI
                                     │                       ▲
                                     │                       │
                                     └─ anomaly + KPI services ┘
```

Full architecture, design decisions, and cloud-migration paths live in
the [`docs/`](docs/) folder.

## Phases

| Phase | Deliverable | Where |
|---|---|---|
| 1 — Scaffold | Structure, `.env`, docker-compose | [`docker/`](docker/), [`.env.example`](.env.example) |
| 2 — Data model | 8-table MySQL schema + 80 seeded products | [`database/`](database/) |
| 3 — Order generator | Faker + Kafka + burst injection | [`generator/`](generator/order_producer.py) |
| 4 — Spark streaming | Watermarked windows, upsert sinks, inventory + low-stock | [`streaming/`](streaming/stream_processor.py) |
| 5 — Anomaly detection | z-score + Isolation Forest | [`anomaly/`](anomaly/detector.py) |
| 6 — KPI alerts | Threshold-driven, config-as-data | [`kpi/`](kpi/evaluator.py) |
| 7 — Power BI dashboard | 4 pages, 20+ DAX measures, theme | [`dashboard/`](dashboard/) |
| 8 — Orchestration & demo | `orchestrator.py`, `demo_controller.py`, walkthrough | [`scripts/`](scripts/), [`DEMO.md`](DEMO.md) |
| 9 — Docs & deployment | Architecture, learnings, GCP paths | [`docs/`](docs/) |

## Quick start

```bash
# 1. clone, enter directory, create venv
python -m venv .venv
.venv/Scripts/activate               # Windows
# source .venv/bin/activate          # *nix
pip install -r requirements.txt
cp .env.example .env

# 2. bring up Kafka + MySQL (schema + products seed automatically)
docker compose -f docker/docker-compose.yml up -d

# 3. launch every worker
python scripts/orchestrator.py up
python scripts/orchestrator.py status     # verify

# 4. trigger a demo spike
python scripts/demo_controller.py burst --size 60 --duration 15
```

Power BI: open `dashboard/connection.pbids` (DirectQuery, MySQL on
`localhost:3306`, creds from `.env`). Follow
[`dashboard/DASHBOARD_DESIGN.md`](dashboard/DASHBOARD_DESIGN.md) to
build the four pages; paste measures from
[`dashboard/measures.dax`](dashboard/measures.dax).

## Prerequisites

- Python 3.10+ (tested on 3.13)
- Java 17 or 21 (for Spark)
- Docker Desktop
- Power BI Desktop (Windows only — use Power BI Service if on macOS/Linux)

Kafka, Zookeeper, MySQL, and Kafka UI all run from
`docker/docker-compose.yml`.

## Operating the stack

| Command | Effect |
|---|---|
| `python scripts/orchestrator.py up` | docker compose + Spark + workers |
| `python scripts/orchestrator.py status` | component health + docker ps |
| `python scripts/orchestrator.py logs <name> --tail 40` | tail a worker log |
| `python scripts/orchestrator.py down` | stop workers + compose down |
| `python scripts/demo_controller.py burst` | fire a revenue-spike demo |
| `python scripts/demo_controller.py drain --product 1001` | fire a low-stock demo |
| `python scripts/demo_controller.py clear-alerts` | reset alerts table |
| `python scripts/demo_controller.py reset-stock` | restore seeded stock |

## Power BI data sources

Connect to MySQL in **DirectQuery** mode. Tables:

| Table | Role |
|---|---|
| `orders`, `order_items` | Row-level facts |
| `products` | Dimension: category, stock, thresholds |
| `sales_metrics` | Minute-level revenue + order count |
| `product_sales_metrics` | Minute-level per-product sales |
| `alerts` | `LOW_STOCK`, `REVENUE_SPIKE`, `KPI_VIOLATION` |
| `kpi_thresholds` | Dimension for KPI cards |

Relationships (one-to-many):
`orders → order_items`,
`products → order_items`,
`products → product_sales_metrics`.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system diagram, data flow, design calls
- [`docs/LEARNINGS.md`](docs/LEARNINGS.md) — non-obvious decisions and trade-offs
- [`docs/CLOUD_DEPLOYMENT.md`](docs/CLOUD_DEPLOYMENT.md) — GCP / BigQuery / Railway paths
- [`docs/LINKEDIN_POST.md`](docs/LINKEDIN_POST.md) — portfolio / promotion template
- [`DEMO.md`](DEMO.md) — beat-by-beat recording script

## Layout

```
generator/   Faker + Kafka producer, shared config
streaming/   Spark Structured Streaming job
database/    schema.sql, seed_products.sql
docker/      docker-compose.yml
anomaly/     detector.py (z-score + Isolation Forest)
kpi/         evaluator.py (threshold-driven)
dashboard/   Power BI assets: .pbids, DAX, M queries, theme, design doc
scripts/     orchestrator, demo controller, verify setup
docs/        architecture, learnings, cloud, promotion
```

## Why this project

The generator sits at one end, Power BI at the other, and in between
there's a real streaming system: Kafka for the bus, Spark for the
aggregation, a staging-table upsert for idempotency, two-strategy
anomaly detection, and a KPI layer that treats SLOs as data rather
than code. The build log is in
[`docs/LEARNINGS.md`](docs/LEARNINGS.md).
