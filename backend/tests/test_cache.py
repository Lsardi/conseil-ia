"""Tests du service de cache."""

from __future__ import annotations

import pytest

from app.services.cache import CacheService


@pytest.fixture
def cache():
    """Cache avec Firestore désactivé pour les tests."""
    service = CacheService()
    service._enabled = True
    service._firestore_available = False
    return service


@pytest.mark.asyncio
async def test_cache_miss(cache: CacheService) -> None:
    """Un cache vide retourne None."""
    result = await cache.get("question", ["claude"], "synthesis")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_and_get(cache: CacheService) -> None:
    """Set puis get retourne les données."""
    data = {"synthesis": "test response"}
    await cache.set("question", ["claude"], "synthesis", data)
    result = await cache.get("question", ["claude"], "synthesis")
    assert result == data


@pytest.mark.asyncio
async def test_cache_different_keys(cache: CacheService) -> None:
    """Des questions différentes ont des clés différentes."""
    await cache.set("question1", ["claude"], "synthesis", {"data": 1})
    await cache.set("question2", ["claude"], "synthesis", {"data": 2})

    r1 = await cache.get("question1", ["claude"], "synthesis")
    r2 = await cache.get("question2", ["claude"], "synthesis")
    assert r1 == {"data": 1}
    assert r2 == {"data": 2}


@pytest.mark.asyncio
async def test_cache_stats(cache: CacheService) -> None:
    """Les stats du cache sont cohérentes."""
    await cache.get("miss", ["claude"], "synthesis")
    await cache.set("hit", ["claude"], "synthesis", {"data": 1})
    await cache.get("hit", ["claude"], "synthesis")

    stats = cache.stats
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 50.0


@pytest.mark.asyncio
async def test_cache_disabled() -> None:
    """Un cache désactivé retourne toujours None."""
    cache = CacheService()
    cache._enabled = False
    await cache.set("q", ["claude"], "synthesis", {"data": 1})
    result = await cache.get("q", ["claude"], "synthesis")
    assert result is None


@pytest.mark.asyncio
async def test_cache_clear(cache: CacheService) -> None:
    """Clear vide le cache."""
    await cache.set("q", ["claude"], "synthesis", {"data": 1})
    await cache.clear()
    result = await cache.get("q", ["claude"], "synthesis")
    assert result is None
