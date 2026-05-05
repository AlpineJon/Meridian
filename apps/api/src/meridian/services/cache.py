"""Redis cache wrapper used by adapters.

Keys are namespaced by adapter (e.g. `meridian:census_acs:msa:12940:2023`).
TTL defaults come from settings (per-source values in .env).
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis_async

from meridian.config import get_settings

_settings = get_settings()
_client: redis_async.Redis | None = None


def get_client() -> redis_async.Redis:
    global _client
    if _client is None:
        _client = redis_async.from_url(_settings.redis_url, decode_responses=True)
    return _client


async def get_json(key: str) -> Any | None:
    raw = await get_client().get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_json(key: str, value: Any, ttl: int) -> None:
    await get_client().set(key, json.dumps(value, default=str), ex=ttl)


async def ping() -> bool:
    try:
        return bool(await get_client().ping())
    except Exception:
        return False
