"""Shared configuration loaded from environment."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.example")


def _get(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _get_float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _get_bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class KafkaConfig:
    bootstrap_servers: str = _get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    orders_topic: str = _get("KAFKA_ORDERS_TOPIC", "orders")
    inventory_topic: str = _get("KAFKA_INVENTORY_TOPIC", "inventory-updates")


@dataclass(frozen=True)
class MySQLConfig:
    host: str = _get("MYSQL_HOST", "localhost")
    port: int = _get_int("MYSQL_PORT", 3306)
    user: str = _get("MYSQL_USER", "ecom_user")
    password: str = _get("MYSQL_PASSWORD", "ecom_pass")
    database: str = _get("MYSQL_DATABASE", "ecommerce_rt")

    @property
    def jdbc_url(self) -> str:
        return (
            f"jdbc:mysql://{self.host}:{self.port}/{self.database}"
            "?useSSL=false&serverTimezone=UTC&rewriteBatchedStatements=true"
        )

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class FakeStoreConfig:
    base_url: str = _get("FAKESTORE_BASE_URL", "https://fakestoreapi.com")
    sync_interval: int = _get_int("CATALOG_SYNC_INTERVAL", 300)


@dataclass(frozen=True)
class APIConfig:
    host: str = _get("API_HOST", "0.0.0.0")
    port: int = _get_int("API_PORT", 8000)
    order_min: float = _get_float("ORDER_RATE_MIN_SECONDS", 2.0)
    order_max: float = _get_float("ORDER_RATE_MAX_SECONDS", 5.0)


@dataclass(frozen=True)
class GeneratorConfig:
    """Legacy Faker generator (kept for fallback); superseded by the FastAPI service."""
    interval_min: int = _get_int("ORDER_INTERVAL_MIN", 2)
    interval_max: int = _get_int("ORDER_INTERVAL_MAX", 5)
    burst_enabled: bool = _get_bool("BURST_ENABLED", True)
    burst_every_seconds: int = _get_int("BURST_EVERY_SECONDS", 180)
    burst_size: int = _get_int("BURST_SIZE", 30)
    burst_duration: int = _get_int("BURST_DURATION_SECONDS", 10)


@dataclass(frozen=True)
class BurstConfig:
    enabled: bool = _get_bool("BURST_ENABLED", True)
    every_seconds: int = _get_int("BURST_EVERY_SECONDS", 180)
    size: int = _get_int("BURST_SIZE", 30)
    duration: int = _get_int("BURST_DURATION_SECONDS", 10)


@dataclass(frozen=True)
class AnomalyConfig:
    check_interval: int = _get_int("ANOMALY_CHECK_INTERVAL", 60)
    window_minutes: int = _get_int("ANOMALY_WINDOW_MINUTES", 30)
    method: str = _get("ANOMALY_METHOD", "isolation_forest")


@dataclass(frozen=True)
class KPIConfig:
    check_interval: int = _get_int("KPI_CHECK_INTERVAL", 60)


KAFKA = KafkaConfig()
MYSQL = MySQLConfig()
FAKESTORE = FakeStoreConfig()
API = APIConfig()
GENERATOR = GeneratorConfig()
BURST = BurstConfig()
ANOMALY = AnomalyConfig()
KPI = KPIConfig()
