"""
Revenue-spike anomaly detector.

Polls sales_metrics every ANOMALY_CHECK_INTERVAL seconds.
Two strategies:
  * z-score: flag the latest minute where revenue > mean + 3*std of the
    trailing window (fast, cheap, works with little data).
  * isolation_forest: train on the last 24h of per-minute revenue and
    flag outliers in the latest window (more robust once data exists).

Detections are written to the alerts table as REVENUE_SPIKE rows.
"""
from __future__ import annotations

import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import mysql.connector
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.config import ANOMALY, MYSQL  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] anomaly: %(message)s",
)
log = logging.getLogger("anomaly")

_shutdown = False


def _handle_signal(signum, frame):  # noqa: ARG001
    global _shutdown
    log.info("Signal %s received, stopping detector", signum)
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


def _load_window(minutes: int) -> pd.DataFrame:
    since = datetime.utcnow() - timedelta(minutes=minutes)
    conn = _connect()
    try:
        df = pd.read_sql(
            """
            SELECT window_start, revenue, order_count
            FROM sales_metrics
            WHERE window_start >= %(since)s
            ORDER BY window_start
            """,
            conn,
            params={"since": since},
        )
    finally:
        conn.close()
    df["revenue"] = df["revenue"].astype(float)
    return df


def _already_alerted(window_start) -> bool:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM alerts
            WHERE alert_type = 'REVENUE_SPIKE'
              AND entity_id = %s
              AND detected_at > (NOW() - INTERVAL 30 MINUTE)
            """,
            (str(window_start),),
        )
        count = cur.fetchone()[0]
    finally:
        conn.close()
    return count > 0


def _insert_alert(
    severity: str,
    window_start,
    detected: float,
    expected_low: float,
    expected_high: float,
    method: str,
) -> None:
    conn = _connect()
    try:
        cur = conn.cursor()
        msg = (
            f"Revenue spike via {method}: ${detected:.2f} at {window_start} "
            f"(expected ${expected_low:.2f}-${expected_high:.2f})"
        )
        cur.execute(
            """
            INSERT INTO alerts
                (alert_type, severity, entity_type, entity_id, message,
                 detected_value, expected_low, expected_high)
            VALUES ('REVENUE_SPIKE', %s, 'WINDOW', %s, %s, %s, %s, %s)
            """,
            (severity, str(window_start), msg, detected, expected_low, expected_high),
        )
        conn.commit()
    finally:
        conn.close()
    log.warning("ALERT inserted: %s", msg)


# ---------------------------------------------------------------------------
# Detection strategies
# ---------------------------------------------------------------------------

def detect_zscore(df: pd.DataFrame) -> None:
    if len(df) < 5:
        return
    latest = df.iloc[-1]
    history = df.iloc[:-1]
    mean = history["revenue"].mean()
    std = history["revenue"].std(ddof=0)
    if std == 0 or np.isnan(std):
        return
    z = (latest["revenue"] - mean) / std
    log.info(
        "[zscore] window=%s rev=$%.2f mean=$%.2f std=$%.2f z=%.2f",
        latest["window_start"], latest["revenue"], mean, std, z,
    )
    if z >= 3.0 and not _already_alerted(latest["window_start"]):
        severity = "CRITICAL" if z >= 5 else "HIGH"
        _insert_alert(
            severity=severity,
            window_start=latest["window_start"],
            detected=float(latest["revenue"]),
            expected_low=float(max(0.0, mean - 3 * std)),
            expected_high=float(mean + 3 * std),
            method=f"z-score z={z:.2f}",
        )


def detect_isolation_forest(df: pd.DataFrame) -> None:
    if len(df) < 15:
        # fall back to z-score until enough history
        detect_zscore(df)
        return

    X = df[["revenue", "order_count"]].to_numpy()
    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=150,
    )
    model.fit(X)
    scores = model.decision_function(X)
    preds = model.predict(X)  # -1 = anomaly

    latest_idx = len(df) - 1
    latest = df.iloc[latest_idx]
    is_anomaly = preds[latest_idx] == -1
    # only flag high-side spikes; low revenue drops go through KPI evaluator
    if is_anomaly and latest["revenue"] > df["revenue"].median():
        mean = df["revenue"].mean()
        std = df["revenue"].std(ddof=0)
        if _already_alerted(latest["window_start"]):
            return
        severity = "CRITICAL" if scores[latest_idx] < -0.2 else "HIGH"
        _insert_alert(
            severity=severity,
            window_start=latest["window_start"],
            detected=float(latest["revenue"]),
            expected_low=float(max(0.0, mean - 2 * std)),
            expected_high=float(mean + 2 * std),
            method=f"isolation_forest score={scores[latest_idx]:.3f}",
        )
    else:
        log.info(
            "[iforest] window=%s rev=$%.2f score=%.3f anomaly=%s",
            latest["window_start"],
            latest["revenue"],
            scores[latest_idx],
            is_anomaly,
        )


def run_once(method: str) -> None:
    # pull plenty of history for IF, less for z-score
    minutes = 24 * 60 if method == "isolation_forest" else ANOMALY.window_minutes
    df = _load_window(minutes)
    if df.empty:
        log.info("No sales_metrics data yet.")
        return
    if method == "zscore":
        detect_zscore(df)
    else:
        detect_isolation_forest(df)


def run() -> None:
    log.info(
        "Anomaly detector starting (method=%s, interval=%ds)",
        ANOMALY.method,
        ANOMALY.check_interval,
    )
    while not _shutdown:
        try:
            run_once(ANOMALY.method)
        except Exception:  # noqa: BLE001
            log.exception("Detector iteration failed; continuing")
        for _ in range(ANOMALY.check_interval):
            if _shutdown:
                break
            time.sleep(1)


if __name__ == "__main__":
    run()
