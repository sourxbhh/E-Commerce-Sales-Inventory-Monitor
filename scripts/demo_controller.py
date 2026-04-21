"""
On-demand demo triggers that talk to the FastAPI live-edge.

    python scripts/demo_controller.py burst --size 60
        -> POST /trigger/burst; the API injects a flash-sale burst
           into the same stream Spark + the anomaly detector watch.

    python scripts/demo_controller.py drain --product 1 --times 30
        -> POST /trigger/drain; forces repeated orders for one SKU
           until stock crosses the reorder threshold (LOW_STOCK).

    python scripts/demo_controller.py clear-alerts
        -> direct SQL: mark all alerts resolved (clean slate).

    python scripts/demo_controller.py list-products
        -> quick peek at the real FakeStoreAPI catalog.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.config import API, MYSQL  # noqa: E402

API_BASE = f"http://localhost:{API.port}"


def _burst(size: int) -> None:
    r = httpx.post(f"{API_BASE}/trigger/burst", params={"size": size}, timeout=10)
    r.raise_for_status()
    print(r.json())


def _drain(product_id: int, times: int) -> None:
    r = httpx.post(
        f"{API_BASE}/trigger/drain",
        params={"product_id": product_id, "times": times},
        timeout=10,
    )
    r.raise_for_status()
    print(r.json())


def _list_products() -> None:
    r = httpx.get(f"{API_BASE}/products", timeout=10)
    r.raise_for_status()
    for p in r.json():
        print(
            f"  {p['product_id']:<4} "
            f"${p['price']:>7.2f}  "
            f"w={p['popularity_weight']:<4}  "
            f"[{p['category']}]  "
            f"{p['name'][:80]}"
        )


def _clear_alerts() -> None:
    conn = mysql.connector.connect(
        host=MYSQL.host,
        port=MYSQL.port,
        user=MYSQL.user,
        password=MYSQL.password,
        database=MYSQL.database,
    )
    try:
        cur = conn.cursor()
        cur.execute("UPDATE alerts SET resolved = 1 WHERE resolved = 0")
        conn.commit()
        print(f"resolved {cur.rowcount} alerts")
    finally:
        conn.close()


def _reset_stock() -> None:
    """Re-run fakestore_sync with --reset. Wipes facts and restores stock."""
    import subprocess
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv" / ("Scripts/python.exe"
                                if sys.platform == "win32"
                                else "bin/python")
    subprocess.run(
        [str(python), str(root / "scripts" / "fakestore_sync.py"), "--reset"],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("burst", help="Flash-sale burst to trigger REVENUE_SPIKE")
    b.add_argument("--size", type=int, default=60)

    d = sub.add_parser("drain", help="Hammer one SKU to trigger LOW_STOCK")
    d.add_argument("--product", type=int, required=True)
    d.add_argument("--times", type=int, default=40)

    sub.add_parser("list-products", help="Show hydrated catalog")
    sub.add_parser("clear-alerts",  help="Mark all alerts resolved")
    sub.add_parser("reset-stock",   help="Wipe facts + re-sync catalog")

    args = parser.parse_args()
    if args.cmd == "burst":
        _burst(args.size)
    elif args.cmd == "drain":
        _drain(args.product, args.times)
    elif args.cmd == "list-products":
        _list_products()
    elif args.cmd == "clear-alerts":
        _clear_alerts()
    elif args.cmd == "reset-stock":
        _reset_stock()


if __name__ == "__main__":
    main()
