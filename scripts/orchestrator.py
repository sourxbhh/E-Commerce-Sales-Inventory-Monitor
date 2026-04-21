"""
Cross-platform launcher for the whole stack.

    python scripts/orchestrator.py up      # boot everything
    python scripts/orchestrator.py down    # stop all services
    python scripts/orchestrator.py status  # show component health
    python scripts/orchestrator.py logs api --tail 40

Components (post-FakeStoreAPI migration):
    spark     - Structured Streaming job consuming Kafka -> MySQL
    api       - FastAPI live-edge (real catalog, generator, WS)
    anomaly   - z-score + IsolationForest detector
    kpi       - threshold-driven KPI evaluator

On `up`, the orchestrator also runs a one-shot scripts/fakestore_sync.py
to hydrate the products table from fakestoreapi.com before launching
the FastAPI service.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
REGISTRY = ROOT / ".orchestrator.json"
COMPOSE = ROOT / "docker" / "docker-compose.yml"

IS_WINDOWS = platform.system() == "Windows"
PYTHON = str(
    ROOT / ".venv" / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")
)

SPARK_PACKAGES = (
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,"
    "com.mysql:mysql-connector-j:8.4.0"
)

COMPONENTS = ["spark", "api", "anomaly", "kpi"]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _load_registry() -> Dict[str, int]:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {}


def _save_registry(reg: Dict[str, int]) -> None:
    REGISTRY.write_text(json.dumps(reg, indent=2))


def _wait_port(host: str, port: int, timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if IS_WINDOWS:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, check=False,
            )
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _spawn(name: str, cmd: List[str], cwd: Path = ROOT) -> int:
    LOGS.mkdir(exist_ok=True)
    log_path = LOGS / f"{name}.log"
    log_f = open(log_path, "ab")
    creationflags = 0
    if IS_WINDOWS:
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
    )
    print(f"  started {name} (pid={proc.pid}) -> {log_path}")
    return proc.pid


def _kill(pid: int) -> None:
    if not _pid_alive(pid):
        return
    try:
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], check=False)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception as e:  # noqa: BLE001
        print(f"  kill {pid} failed: {e}")


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_up() -> None:
    LOGS.mkdir(exist_ok=True)
    print(">> docker compose up")
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE), "up", "-d"],
        check=True,
    )

    print(">> waiting for Kafka on :9092")
    if not _wait_port("localhost", 9092, 120):
        print("!! Kafka did not come up in time")
        sys.exit(1)

    print(">> waiting for MySQL on :3306")
    if not _wait_port("localhost", 3306, 120):
        print("!! MySQL did not come up in time")
        sys.exit(1)

    print(">> ensuring topics")
    for topic in ("orders", "inventory-updates"):
        subprocess.run(
            [
                "docker", "exec", "ecom_kafka",
                "kafka-topics", "--bootstrap-server", "kafka:29092",
                "--create", "--if-not-exists",
                "--topic", topic, "--partitions", "3", "--replication-factor", "1",
            ],
            check=False,
        )

    print(">> hydrating product catalog from FakeStoreAPI")
    sync = subprocess.run(
        [PYTHON, str(ROOT / "scripts" / "fakestore_sync.py")],
        cwd=str(ROOT),
        check=False,
    )
    if sync.returncode != 0:
        print("!! catalog sync failed; aborting")
        sys.exit(1)

    reg: Dict[str, int] = {}

    print(">> launching Spark streaming job")
    reg["spark"] = _spawn(
        "spark",
        [
            "spark-submit",
            "--packages", SPARK_PACKAGES,
            "--conf", "spark.sql.session.timeZone=UTC",
            str(ROOT / "streaming" / "stream_processor.py"),
        ],
    )

    print(">> giving Spark 25s to warm up")
    time.sleep(25)

    print(">> launching FastAPI live-edge")
    reg["api"] = _spawn(
        "api",
        [
            PYTHON, "-m", "uvicorn", "api.main:app",
            "--host", "0.0.0.0", "--port", "8000",
        ],
    )

    print(">> waiting for API on :8000")
    if not _wait_port("localhost", 8000, 30):
        print("!! API did not start; check logs/api.log")

    print(">> launching anomaly detector + KPI evaluator")
    reg["anomaly"] = _spawn("anomaly", [PYTHON, "-m", "anomaly.detector"])
    reg["kpi"]     = _spawn("kpi",     [PYTHON, "-m", "kpi.evaluator"])

    _save_registry(reg)
    print()
    print("All components running.")
    print("  http://localhost:8000/health      (live-edge health)")
    print("  http://localhost:8000/docs        (API docs, Swagger UI)")
    print("  ws://localhost:8000/stream/orders (WebSocket order stream)")
    print("  http://localhost:8080             (Kafka UI)")
    print("  python scripts/orchestrator.py status")


def cmd_status() -> None:
    reg = _load_registry()
    print("-- Python workers --")
    for name in COMPONENTS:
        pid = reg.get(name, -1)
        alive = _pid_alive(pid)
        print(f"  {name:<10} pid={pid:<8} alive={alive}")

    print("-- Docker services --")
    subprocess.run(["docker", "compose", "-f", str(COMPOSE), "ps"], check=False)


def cmd_down() -> None:
    reg = _load_registry()
    for name, pid in reg.items():
        print(f">> stopping {name} ({pid})")
        _kill(pid)

    if REGISTRY.exists():
        REGISTRY.unlink()

    print(">> docker compose down")
    subprocess.run(["docker", "compose", "-f", str(COMPOSE), "down"], check=False)


def cmd_logs(name: str, tail: int) -> None:
    log = LOGS / f"{name}.log"
    if not log.exists():
        print(f"(no log file for {name})")
        return
    with open(log, "rb") as f:
        lines = f.read().splitlines()[-tail:]
    for line in lines:
        try:
            print(line.decode("utf-8", errors="replace"))
        except UnicodeDecodeError:
            print(repr(line))


def cmd_resync() -> None:
    subprocess.run(
        [PYTHON, str(ROOT / "scripts" / "fakestore_sync.py")],
        cwd=str(ROOT),
        check=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("up")
    sub.add_parser("down")
    sub.add_parser("status")
    sub.add_parser("resync", help="re-pull product catalog from FakeStoreAPI")
    logs = sub.add_parser("logs")
    logs.add_argument("name", choices=COMPONENTS)
    logs.add_argument("--tail", type=int, default=40)

    args = parser.parse_args()
    if args.cmd == "up":
        cmd_up()
    elif args.cmd == "down":
        cmd_down()
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "resync":
        cmd_resync()
    elif args.cmd == "logs":
        cmd_logs(args.name, args.tail)


if __name__ == "__main__":
    main()
