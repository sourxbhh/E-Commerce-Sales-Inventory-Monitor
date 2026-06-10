"""API tests via FastAPI TestClient against the fixture marts."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture
def client(pipeline_db):
    from api.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["fct_orders_rows"] == 5


def test_kpis(client):
    r = client.get("/kpis")
    assert r.status_code == 200
    body = r.json()
    assert body["total_orders"] == 5
    # 110 + 55 + 220 + 82.5 + 132  (order_value = items + freight)
    assert body["total_revenue"] == pytest.approx(110 + 55 + 220 + 82.5 + 132)


def test_by_state(client):
    rows = client.get("/kpis/by-state").json()
    states = {r["customer_state"] for r in rows}
    assert states == {"SP", "RJ"}


def test_top_categories(client):
    rows = client.get("/kpis/top-categories?limit=2").json()
    assert len(rows) == 2
    assert {"product_category", "items_sold", "revenue"} <= set(rows[0])
