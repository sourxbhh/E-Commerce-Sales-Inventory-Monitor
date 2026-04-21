# Key learnings

A running log of the non-obvious calls made while building this.

## Streaming

- **Watermarks are mandatory for aggregates.** Without one, Spark
  keeps unbounded state and the driver eventually OOMs. The 10-min
  watermark here trades some late-order tolerance for bounded state.
- **Explicit schema beats inference on Kafka.** `from_json` with an
  inferred schema samples the first micro-batch, which is brittle.
  The schema in `stream_processor.py` is the contract.
- **`foreachBatch` is the right sink for multi-destination writes.**
  The batch DF can be reused for JDBC writes, raw SQL, and alert
  generation without re-reading Kafka.
- **Spark JDBC has no upsert.** Every "real" pipeline ends up with a
  staging-table pattern (`_stg_*` + `ON DUPLICATE KEY UPDATE`). This
  also makes the pipeline re-runnable — replaying a Kafka offset is
  safe.

## Power BI

- **Import vs DirectQuery**: Import gives better perf and time
  intelligence but refreshes on a schedule (15-min minimum on most
  licences). DirectQuery hits MySQL live, so a burst shows up in
  under a minute — the whole point of this dashboard.
- **Pre-aggregate everywhere.** Page 1 does not compute
  revenue-per-minute on the fly from `orders`; it reads
  `sales_metrics`, which Spark already aggregated. DirectQuery
  latency stays low because the expensive work already happened.
- **Page refresh is set per-page**, not globally. Page 1 refreshes at
  60s; Pages 2 and 3 can be slower because category/stock views
  aren't second-critical.
- **Conditional formatting by measure** (the `Severity Color` /
  `Stock Row Color` measures) is more reusable than hard-coded
  rules in each visual.

## Anomaly detection

- **Z-score for cold start** matters. Isolation Forest needs ≥15
  samples before it produces useful outputs; with minute windows
  that's a 15-minute dead zone where the detector would otherwise be
  silent.
- **Direction matters.** `IsolationForest` flags both under- and
  over-revenue. For spike detection we only care about the high side
  of the median; low-side drops are handled by the KPI evaluator's
  `revenue_drop_pct`, which has business-meaningful thresholds.
- **Dedupe by window_start.** Without the 30-minute dedupe guard,
  the detector would re-alert every 60s on the same spike window
  until it fell off the trailing view.

## KPI alerts

- **Config as data.** Putting thresholds in `kpi_thresholds` means a
  BA can tune SLOs via SQL (or a small admin UI later) without
  touching Python. The operator wins; the engineer stops getting
  paged to change `>= 500`.
- **Don't collapse severity.** Warning and Critical are separate
  alert rows with separate dedupes so a situation degrading from
  warning → critical produces a visible second alert.

## Operational

- **Checkpoints live under `./checkpoints/main/`.** Delete to reset
  the Kafka offset; otherwise the Spark job resumes from where it
  left off after a restart, which is usually what you want.
- **Python 3.13 + PySpark 3.5.3 works** with Java 21, but requires
  building the pyspark wheel from source (pip does this automatically).
- **`confluent-kafka` beats `kafka-python`** on Windows and is
  maintained; `kafka-python` has lagged on newer Python versions.
