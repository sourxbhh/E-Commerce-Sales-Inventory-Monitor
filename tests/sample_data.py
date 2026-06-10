"""
Tiny, referentially-consistent Olist fixture used by the test suite and CI.

Mirrors the *raw* CSV column names (including the original `lenght` typos and the
per-order customer_id grain) so it flows through the real loader, dbt models, GE
suites, and API unchanged — just on a handful of rows instead of ~100k.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# 5 orders, one customer each (Olist's per-order customer grain), 3 products,
# 2 sellers, 2 zip prefixes. All FKs resolve.
_ORDER_IDS = [f"order{i}" for i in range(1, 6)]
_CUST_IDS = [f"cust{i}" for i in range(1, 6)]
_PRODUCTS = ["prodA", "prodB", "prodC"]
_SELLERS = ["sell1", "sell2"]


def _raw_tables() -> dict[str, pd.DataFrame]:
    orders = pd.DataFrame({
        "order_id": _ORDER_IDS,
        "customer_id": _CUST_IDS,
        "order_status": ["delivered", "delivered", "delivered", "shipped", "canceled"],
        "order_purchase_timestamp": [
            "2017-01-05 10:00:00", "2017-02-10 11:30:00", "2017-03-15 09:15:00",
            "2017-04-20 14:00:00", "2017-05-25 16:45:00",
        ],
        "order_approved_at": [
            "2017-01-05 10:20:00", "2017-02-10 12:00:00", "2017-03-15 09:40:00",
            "2017-04-20 14:30:00", "2017-05-25 17:00:00",
        ],
        "order_delivered_carrier_date": [
            "2017-01-06 08:00:00", "2017-02-11 08:00:00", "2017-03-16 08:00:00",
            "2017-04-21 08:00:00", None,
        ],
        "order_delivered_customer_date": [
            "2017-01-10 18:00:00", "2017-02-20 18:00:00", "2017-03-19 18:00:00",
            None, None,
        ],
        "order_estimated_delivery_date": [
            "2017-01-15 00:00:00", "2017-02-18 00:00:00", "2017-03-25 00:00:00",
            "2017-04-30 00:00:00", "2017-06-01 00:00:00",
        ],
    })

    order_items = pd.DataFrame({
        "order_id": _ORDER_IDS,
        "order_item_id": [1, 1, 1, 1, 1],
        "product_id": ["prodA", "prodB", "prodC", "prodA", "prodB"],
        "seller_id": ["sell1", "sell2", "sell1", "sell2", "sell1"],
        "shipping_limit_date": [
            "2017-01-08 10:00:00", "2017-02-13 10:00:00", "2017-03-18 10:00:00",
            "2017-04-23 10:00:00", "2017-05-28 10:00:00",
        ],
        "price": [100.0, 50.0, 200.0, 75.0, 120.0],
        "freight_value": [10.0, 5.0, 20.0, 7.5, 12.0],
    })

    order_payments = pd.DataFrame({
        "order_id": _ORDER_IDS,
        "payment_sequential": [1, 1, 1, 1, 1],
        "payment_type": ["credit_card", "boleto", "credit_card", "voucher", "credit_card"],
        "payment_installments": [3, 1, 6, 1, 2],
        "payment_value": [110.0, 55.0, 220.0, 82.5, 132.0],
    })

    order_reviews = pd.DataFrame({
        "review_id": [f"rev{i}" for i in range(1, 6)],
        "order_id": _ORDER_IDS,
        "review_score": [5, 4, 5, 3, 1],
        "review_comment_title": [None, None, "Otimo", None, None],
        "review_comment_message": [None, "bom", None, None, "ruim"],
        "review_creation_date": [
            "2017-01-11 00:00:00", "2017-02-21 00:00:00", "2017-03-20 00:00:00",
            "2017-04-25 00:00:00", "2017-05-30 00:00:00",
        ],
        "review_answer_timestamp": [
            "2017-01-12 00:00:00", "2017-02-22 00:00:00", "2017-03-21 00:00:00",
            "2017-04-26 00:00:00", "2017-05-31 00:00:00",
        ],
    })

    customers = pd.DataFrame({
        "customer_id": _CUST_IDS,
        "customer_unique_id": [f"uniq{i}" for i in range(1, 6)],
        "customer_zip_code_prefix": ["01001", "02002", "01001", "02002", "01001"],
        "customer_city": ["sao paulo", "rio", "sao paulo", "rio", "sao paulo"],
        "customer_state": ["SP", "RJ", "SP", "RJ", "SP"],
    })

    products = pd.DataFrame({
        "product_id": _PRODUCTS,
        "product_category_name": ["beleza_saude", "relogios_presentes", "cama_mesa_banho"],
        "product_name_lenght": [40, 55, 33],
        "product_description_lenght": [500, 600, 400],
        "product_photos_qty": [3, 5, 2],
        "product_weight_g": [300.0, 150.0, 1200.0],
        "product_length_cm": [20.0, 10.0, 40.0],
        "product_height_cm": [10.0, 5.0, 20.0],
        "product_width_cm": [15.0, 8.0, 30.0],
    })

    sellers = pd.DataFrame({
        "seller_id": _SELLERS,
        "seller_zip_code_prefix": ["01001", "02002"],
        "seller_city": ["sao paulo", "rio"],
        "seller_state": ["SP", "RJ"],
    })

    geolocation = pd.DataFrame({
        "geolocation_zip_code_prefix": ["01001", "01001", "02002"],
        "geolocation_lat": [-23.55, -23.56, -22.90],
        "geolocation_lng": [-46.63, -46.64, -43.20],
        "geolocation_city": ["sao paulo", "sao paulo", "rio"],
        "geolocation_state": ["SP", "SP", "RJ"],
    })

    translation = pd.DataFrame({
        "product_category_name": ["beleza_saude", "relogios_presentes", "cama_mesa_banho"],
        "product_category_name_english": ["health_beauty", "watches_gifts", "bed_bath_table"],
    })

    return {
        "orders": orders,
        "order_items": order_items,
        "order_payments": order_payments,
        "order_reviews": order_reviews,
        "customers": customers,
        "products": products,
        "sellers": sellers,
        "geolocation": geolocation,
        "product_category_name_translation": translation,
    }


def write_processed_parquet(dest: Path) -> Path:
    """Write the fixture to dest/<table>/part-0.parquet (the loader's layout)."""
    dest = Path(dest)
    for name, df in _raw_tables().items():
        table_dir = dest / name
        table_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(table_dir / "part-0.parquet", index=False)
    return dest


if __name__ == "__main__":
    import sys

    out = write_processed_parquet(Path(sys.argv[1] if len(sys.argv) > 1 else "data/processed"))
    print(f"wrote fixture to {out}")
