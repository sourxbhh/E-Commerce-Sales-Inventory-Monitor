"""Central env-driven settings shared by all ingestion / streaming code."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    # Paths
    raw_dir: Path = ROOT / "data" / "raw"
    processed_dir: Path = ROOT / "data" / "processed"

    # Azure
    azure_storage_account: str = ""
    azure_storage_container: str = "raw"
    azure_storage_key: str = ""
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # Warehouse (DuckDB)
    duckdb_path: Path = ROOT / "warehouse" / "olist.duckdb"
    warehouse_schema_raw: str = "raw"
    warehouse_schema_staging: str = "staging"
    warehouse_schema_marts: str = "marts"

    @property
    def adls_account_url(self) -> str:
        return f"https://{self.azure_storage_account}.dfs.core.windows.net"


settings = Settings()
