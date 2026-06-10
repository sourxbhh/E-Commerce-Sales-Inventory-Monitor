# Slim image for the FastAPI metrics service. The DuckDB warehouse is provided
# at runtime (bind mount / volume at /app/warehouse/olist.duckdb), not baked in.
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    "uvicorn[standard]==0.32.0" \
    duckdb==1.1.3 \
    pydantic==2.9.2 \
    pydantic-settings==2.6.1 \
    python-dotenv==1.0.1

COPY ingestion/ ingestion/
COPY api/ api/

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
