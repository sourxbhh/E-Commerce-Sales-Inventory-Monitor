"""
Shared fixtures. `pipeline_db` runs the *real* pipeline (loader + dbt) against a
tiny synthetic fixture in a temp warehouse, so integration tests exercise the
production code paths without the ~100k-row Olist dataset.
"""
from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pytest

from ingestion.config import settings
from tests.sample_data import write_processed_parquet

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "warehouse"


@pytest.fixture(scope="session")
def pipeline_db(tmp_path_factory) -> Path:
    tmp = tmp_path_factory.mktemp("warehouse")
    processed = tmp / "processed"
    duckdb_path = tmp / "olist.duckdb"

    write_processed_parquet(processed)

    # Point the shared settings + dbt at the temp warehouse for this session.
    orig_processed, orig_duckdb = settings.processed_dir, settings.duckdb_path
    settings.processed_dir = processed
    settings.duckdb_path = duckdb_path
    os.environ["DUCKDB_PATH"] = str(duckdb_path)

    from batch.load_duckdb import load

    load()

    from dbt.cli.main import dbtRunner

    res = dbtRunner().invoke([
        "build",
        "--project-dir", str(WAREHOUSE),
        "--profiles-dir", str(WAREHOUSE),
        "--no-partial-parse",
    ])
    assert res.success, "dbt build failed on fixture data"

    yield duckdb_path

    settings.processed_dir, settings.duckdb_path = orig_processed, orig_duckdb
    os.environ.pop("DUCKDB_PATH", None)


@pytest.fixture
def con(pipeline_db) -> duckdb.DuckDBPyConnection:
    c = duckdb.connect(str(pipeline_db), read_only=True)
    yield c
    c.close()
