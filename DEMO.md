# Demo walkthrough (Phase 8)

A scripted 3-5 minute run that exercises every visible piece of the
pipeline. Rehearse once; you'll record it in one take.

## Pre-roll checklist (do before hitting record)

- Docker Desktop running.
- Power BI Desktop open to `dashboard/EcomRealtimeMonitor.pbix`.
- Pages 1 and 4 have **Page refresh = 1 minute**.
- All four components running:

  ```bash
  python scripts/orchestrator.py up
  python scripts/orchestrator.py status
  ```

- Fresh state:

  ```bash
  python scripts/demo_controller.py clear-alerts
  python scripts/demo_controller.py reset-stock
  ```

- Wait ~3 minutes so `sales_metrics` has baseline data for the
  Isolation Forest model to learn "normal" from.

## Recording beats

| Time | Screen | Narration cue |
|---|---|---|
| 0:00 | Terminal, architecture diagram page | "End-to-end streaming pipeline — generator, Kafka, Spark, MySQL, Power BI." |
| 0:20 | `orchestrator.py status` | "Four services up; Spark streaming, generator, anomaly detector, KPI evaluator." |
| 0:35 | Power BI Page 1 | Point at revenue-per-minute line climbing steadily. |
| 1:00 | Terminal | `python scripts/demo_controller.py burst --size 60 --duration 15` |
| 1:05 | Power BI Page 1 | Watch the revenue line jump; card colour flips. |
| 1:20 | Power BI Page 4 | Scatter overlay shows red dot; alert log shows new REVENUE_SPIKE row. |
| 1:45 | Terminal | `python scripts/demo_controller.py drain --product 1001 --times 30` |
| 2:00 | Power BI Page 3 | Wireless Earbuds Pro goes red; reorder suggestion appears. |
| 2:15 | Power BI Page 4 | LOW_STOCK alert row appears with matching severity colour. |
| 2:30 | Terminal | `python scripts/orchestrator.py logs anomaly --tail 15` — show the detection log. |
| 2:50 | README architecture image | "Everything else is just Python, Spark, and DAX." |
| 3:00 | end | "Link to repo in the description." |

## What to say (talking points)

- **Why Kafka**: decouples generator from consumer; re-playable; the
  standard data-engineering source.
- **Why Structured Streaming**: exactly-once semantics via
  checkpointing, watermarks for late data, same API as batch.
- **Why DirectQuery, not Import**: Import would refresh on Power BI's
  schedule (minimum 15 min); DirectQuery hits MySQL live, so a burst
  shows up in under a minute.
- **Why two anomaly strategies**: z-score is cheap and works on
  minute 1; Isolation Forest takes over once the table has 15+
  minutes of history so we catch subtler patterns.
- **Why a thresholds table**: lets an analyst tune SLOs without
  redeploying the detector — classic config-as-data.

## Reset for the next take

```bash
python scripts/demo_controller.py clear-alerts
python scripts/demo_controller.py reset-stock
python scripts/orchestrator.py down
rm -rf checkpoints/main      # forces a clean Kafka offset next boot
python scripts/orchestrator.py up
```

## Recording setup

- OBS Studio, 1920×1080, 30 fps.
- Hide personal tabs and notifications.
- Monospace font at 14pt+ in terminals.
- Power BI zoom 100%; full-screen the page (F11) for clean frames.
