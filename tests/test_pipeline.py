"""Integration tests over the loader + dbt marts + GE, on the fixture warehouse."""
import pytest

pytestmark = pytest.mark.integration


def test_raw_tables_loaded(con):
    assert con.execute("select count(*) from raw.orders").fetchone()[0] == 5
    assert con.execute("select count(*) from raw.order_items").fetchone()[0] == 5
    assert con.execute("select count(*) from raw.customers").fetchone()[0] == 5


def test_fct_orders_grain_and_values(con):
    n = con.execute("select count(*) from main_marts.fct_orders").fetchone()[0]
    assert n == 5
    # order1: price 100 + freight 10 = 110
    val = con.execute(
        "select order_value from main_marts.fct_orders where order_id = 'order1'"
    ).fetchone()[0]
    assert val == pytest.approx(110.0)


def test_dim_products_english_category(con):
    cat = con.execute(
        "select product_category from main_marts.dim_products where product_id = 'prodA'"
    ).fetchone()[0]
    assert cat == "health_beauty"


def test_late_flag(con):
    # order2 delivered 2017-02-20, estimated 2017-02-18 -> late
    is_late = con.execute(
        "select is_late from main_marts.fct_orders where order_id = 'order2'"
    ).fetchone()[0]
    assert is_late is True


def test_great_expectations_passes(pipeline_db):
    from quality.validate import validate

    assert validate() is True
