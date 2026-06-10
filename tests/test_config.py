from ingestion.config import Settings


def test_adls_account_url_built_from_account():
    s = Settings(azure_storage_account="acct123")
    assert s.adls_account_url == "https://acct123.dfs.core.windows.net"


def test_defaults_present():
    s = Settings()
    assert s.warehouse_schema_raw == "raw"
    assert s.kafka_topic_orders == "olist.orders"
    assert s.duckdb_path.name == "olist.duckdb"
