"""
Dynamic KPI alert evaluator.

Reads thresholds from kpi_thresholds, computes the live value of each
metric against the configured window, and inserts KPI_VIOLATION rows
into alerts when warning/critical levels are breached. Thresholds can
be tuned without redeploying code.
"""
from __future__ import annotations

import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.config import KPI, MYSQL  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] kpi: %(message)s",
)
log = logging.getLogger("kpi")

_shutdown = False


def _handle_signal(signum, frame):  # noqa: ARG001
    global _shutdown
    log.info("Signal %s received, stopping evaluator", signum)
    _shutdown = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def _connect():
    return mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )


# ---------------------------------------------------------------------------
# Metric calculations -- each returns a single numeric value or None
# ---------------------------------------------------------------------------

def _one(cur, sql: str, params=()) -> Optional[float]:
    cur.execute(sql, params)
    row = cur.fetchone()
    if row is None or row[0] is None:
        return None
    return float(row[0])


def compute_metric(cur, name: str, window_minutes: int) -> Optional[float]:
    since = datetime.utcnow() - timedelta(minutes=window_minutes)

    if name == "revenue_per_5min":
        return _one(
            cur,
            "SELECT COALESCE(SUM(revenue), 0) FROM sales_metrics "
            "WHERE window_start >= %s",
            (since,),
        )
    if name == "orders_per_5min":
        return _one(
            cur,
            "SELECT COALESCE(SUM(order_count), 0) FROM sales_metrics "
            "WHERE window_start >= %s",
            (since,),
        )
    if name == "low_stock_count":
        return _one(
            cur,
            "SELECT COUNT(*) FROM products "
            "WHERE stock_quantity <= reorder_threshold",
        )
    if name == "avg_order_value":
        return _one(
            cur,
            "SELECT COALESCE(AVG(avg_order_value), 0) FROM sales_metrics "
            "WHERE window_start >= %s",
            (since,),
        )
    if name == "revenue_drop_pct":
        prior = since - timedelta(minutes=window_minutes)
        cur.execute(
            "SELECT COALESCE(SUM(revenue), 0) FROM sales_metrics "
            "WHERE window_start >= %s AND window_start < %s",
            (prior, since),
        )
        prior_rev = float(cur.fetchone()[0] or 0)
        cur.execute(
            "SELECT COALESCE(SUM(revenue), 0) FROM sales_metrics "
            "WHERE window_start >= %s",
            (since,),
        )
        current_rev = float(cur.fetchone()[0] or 0)
        if prior_rev <= 0:
            return 0.0
        drop = (prior_rev - current_rev) / prior_rev * 100.0
        return max(drop, 0.0)

    log.warning("Unknown metric: %s", name)
    return None


# ---------------------------------------------------------------------------
# Threshold comparison
# ---------------------------------------------------------------------------

def _breach(value: float, threshold: float, op: str) -> bool:
    if op == "<":
        return value < threshold
    if op == "<=":
        return value <= threshold
    if op == ">":
        return value > threshold
    if op == ">=":
        return value >= threshold
    if op == "==":
        return value == threshold
    return False


def _recent_alert_exists(cur, metric_name: str, severity: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM alerts
        WHERE alert_type = 'KPI_VIOLATION'
          AND entity_id = %s
          AND severity = %s
          AND detected_at > (NOW() - INTERVAL 5 MINUTE)
        LIMIT 1
        """,
        (metric_name, severity),
    )
    return cur.fetchone() is not None


def _insert_kpi_alert(
    cur,
    metric_name: str,
    severity: str,
    value: float,
    threshold: float,
    op: str,
    description: str,
) -> None:
    msg = (
        f"KPI {metric_name} {op} {threshold}: observed {value:.2f}. {description}"
    ).strip()
    cur.execute(
        """
        INSERT INTO alerts
            (alert_type, severity, entity_type, entity_id, message,
             detected_value, expected_low, expected_high)
        VALUES ('KPI_VIOLATION', %s, 'KPI', %s, %s, %s, NULL, %s)
        """,
        (severity, metric_name, msg, value, threshold),
    )
    log.warning("ALERT %s/%s -> %s", severity, metric_name, msg)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def evaluate_once() -> None:
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT metric_name, description, warning_threshold, "
            "critical_threshold, comparison_operator, window_minutes "
            "FROM kpi_thresholds WHERE enabled = 1"
        )
        thresholds = cur.fetchall()

        write_cur = conn.cursor()
        for row in thresholds:
            metric = row["metric_name"]
            window = int(row["window_minutes"])
            op = row["comparison_operator"]
            value = compute_metric(write_cur, metric, window)
            if value is None:
                continue

            critical = row["critical_threshold"]
            warning = row["warning_threshold"]
            severity = None
            threshold_used = None

            if critical is not None and _breach(value, float(critical), op):
                severity, threshold_used = "CRITICAL", float(critical)
            elif warning is not None and _breach(value, float(warning), op):
                severity, threshold_used = "WARNING", float(warning)

            log.info(
                "metric=%s value=%.2f op=%s warn=%s crit=%s -> %s",
                metric, value, op, warning, critical, severity or "OK",
            )

            if severity and not _recent_alert_exists(write_cur, metric, severity):
                _insert_kpi_alert(
                    write_cur,
                    metric_name=metric,
                    severity=severity,
                    value=value,
                    threshold=threshold_used,
                    op=op,
                    description=row["description"] or "",
                )

        conn.commit()
    finally:
        conn.close()


def run() -> None:
    log.info("KPI evaluator starting (interval=%ds)", KPI.check_interval)
    while not _shutdown:
        try:
            evaluate_once()
        except Exception:  # noqa: BLE001
            log.exception("KPI iteration failed; continuing")
        for _ in range(KPI.check_interval):
            if _shutdown:
                break
            time.sleep(1)


if __name__ == "__main__":
    run()
