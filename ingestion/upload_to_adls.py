"""
Upload data/processed/ to Azure Data Lake Storage Gen2 under the configured
container, preserving the local directory layout (table_name/year_month=YYYY-MM/).

Auth resolution order:
  1. AZURE_STORAGE_KEY (account key)            — easy local-dev path
  2. DefaultAzureCredential                     — service principal / az login

Run:
    python -m ingestion.upload_to_adls
    python -m ingestion.upload_to_adls --prefix raw/olist
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

from ingestion.config import settings

log = logging.getLogger("upload_to_adls")
logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(message)s")


def _service_client() -> DataLakeServiceClient:
    if not settings.azure_storage_account:
        raise SystemExit("AZURE_STORAGE_ACCOUNT is not set; check your .env")
    if settings.azure_storage_key:
        log.info("auth: storage account key")
        return DataLakeServiceClient(
            account_url=settings.adls_account_url,
            credential=settings.azure_storage_key,
        )
    log.info("auth: DefaultAzureCredential (service principal / az login)")
    return DataLakeServiceClient(
        account_url=settings.adls_account_url,
        credential=DefaultAzureCredential(),
    )


def _walk(local: Path):
    for p in local.rglob("*"):
        if p.is_file():
            yield p


def upload(prefix: str = "olist") -> None:
    if not settings.processed_dir.exists():
        raise SystemExit(
            f"{settings.processed_dir} does not exist — run "
            f"`python -m ingestion.olist_to_parquet` first"
        )

    svc = _service_client()
    fs = svc.get_file_system_client(settings.azure_storage_container)
    try:
        fs.create_file_system()
        log.info("created container %s", settings.azure_storage_container)
    except Exception:  # already exists
        pass

    n = 0
    total_bytes = 0
    for local_path in _walk(settings.processed_dir):
        rel = local_path.relative_to(settings.processed_dir).as_posix()
        remote = f"{prefix}/{rel}" if prefix else rel
        file_client = fs.get_file_client(remote)
        with open(local_path, "rb") as f:
            data = f.read()
        file_client.upload_data(data, overwrite=True)
        n += 1
        total_bytes += len(data)
        log.info("  → %s (%d bytes)", remote, len(data))

    log.info(
        "uploaded %d files (%.2f MB) to abfss://%s@%s.dfs.core.windows.net/%s/",
        n,
        total_bytes / 1024 / 1024,
        settings.azure_storage_container,
        settings.azure_storage_account,
        prefix,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="olist", help="virtual folder under the container")
    args = ap.parse_args()
    upload(args.prefix)


if __name__ == "__main__":
    main()
