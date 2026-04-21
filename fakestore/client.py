"""
Thin async + sync client for fakestoreapi.com.

Endpoints used:
  GET /products              -> full catalog (20 items)
  GET /products/categories   -> category list
  GET /carts                 -> fake historical carts (used to mine
                                realistic basket size + quantity
                                distributions for the order generator)
"""
from __future__ import annotations

import logging
from typing import List

import httpx

from generator.config import FAKESTORE

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


# ---------- sync versions (used by ingest scripts) ----------

def fetch_products_sync() -> List[dict]:
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.get(f"{FAKESTORE.base_url}/products")
        r.raise_for_status()
        return r.json()


def fetch_carts_sync() -> List[dict]:
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.get(f"{FAKESTORE.base_url}/carts")
        r.raise_for_status()
        return r.json()


def fetch_categories_sync() -> List[str]:
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.get(f"{FAKESTORE.base_url}/products/categories")
        r.raise_for_status()
        return r.json()


# ---------- async versions (used by FastAPI service) ----------

async def fetch_products() -> List[dict]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(f"{FAKESTORE.base_url}/products")
        r.raise_for_status()
        return r.json()


async def fetch_carts() -> List[dict]:
    async with httpx.AsyncClient(timeout=_TIMEOUT) as c:
        r = await c.get(f"{FAKESTORE.base_url}/carts")
        r.raise_for_status()
        return r.json()
