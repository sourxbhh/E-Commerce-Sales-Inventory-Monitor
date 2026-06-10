# Agent guide — Olist Analytics Platform

This is a portfolio-grade data platform on the Olist dataset. The audience is hiring managers reading a Data Analyst / Analytics Engineer resume — so the repo deliberately spans the full modern data stack (S3, Kafka, Spark, dbt, Airflow, GE, Power BI, GitHub Actions, Terraform).

## Working principles

- **No data in git.** All raw / processed datasets stay in `data/` (gitignored) or S3. Never commit CSV / parquet / .duckdb files.
- **Secrets via `.env` only.** `.env.example` is the template. AWS keys, Kaggle creds, and DB passwords must never be hardcoded.
- **Windows-first dev box.** Primary developer is on Windows + PowerShell with a `.venv` at the repo root. Bash is available via the `Bash` tool but PowerShell-friendly commands are preferred for any docs / scripts the user runs by hand.
- **Free-tier hard cap.** Azure ADLS Gen2 (LRS hot) free tier is 5 GB for 12 months. Lifecycle policy moves blobs to **Cool** after 30 days. Don't add anything that incurs charges without flagging it.
- **Cloud is Azure.** Object storage = ADLS Gen2 (`abfss://...`). Auth = storage account key locally, service principal in CI. Provider = Terraform `azurerm`. Spark uses `hadoop-azure` for ADLS access.
- **DuckDB is the default warehouse.** dbt models must stay portable enough that swapping the profile to `dbt-snowflake` is a one-line change. Avoid DuckDB-only SQL functions in mart models.
- **One milestone = one mergeable commit.** Milestones M0–M7 are tracked in [`README.md`](README.md). Each milestone should leave the repo in a runnable state.

## Layout conventions

- Python packages use snake_case folders with an `__init__.py`.
- dbt models: `stg_<source>__<table>.sql`, `int_<concept>.sql`, `fct_*` / `dim_*` for marts.
- Each Python entry point is runnable as `python -m <package>.<module>` and has a `if __name__ == "__main__":` block.
- All scripts read config from env vars via `pydantic-settings`, never hardcoded.

## When in doubt

- Prefer reusing existing files over creating parallel ones.
- Don't scaffold a folder that isn't part of the current milestone — grow into the layout.
- Keep comments rare; let names + dbt model docs do the talking.
