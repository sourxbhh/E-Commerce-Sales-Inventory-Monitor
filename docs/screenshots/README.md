# Screenshots

Drop the following PNGs here and they'll render in the root README's gallery.
These are the manual captures the automated pipeline can't produce on its own.

| File | What to capture | How |
| --- | --- | --- |
| `powerbi-executive.png` | Power BI executive page (cards, revenue trend, state map) | Build from [dashboard/](../../dashboard), screenshot |
| `airflow-dag.png` | `olist_pipeline` graph, all tasks green | `docker compose -f docker/airflow/docker-compose.yml up -d`, open :8080 |
| `api-docs.png` | FastAPI Swagger UI at `/docs` | `uvicorn api.main:app`, open :8000/docs |
| `dbt-docs.png` | dbt lineage graph | `cd warehouse && dbt docs generate && dbt docs serve` |
| `ci-green.png` | GitHub Actions run, all jobs passing | push to GitHub, Actions tab |

Keep them ~1600px wide. Reference them from the root README as
`docs/screenshots/<file>`.
