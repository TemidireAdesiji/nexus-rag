"""Tests for the LRU query result cache."""

from __future__ import annotations

from gateway.storage.cache import QueryResultCache


def test_store_and_lookup(
    cache: QueryResultCache,
) -> None:
    """Stored value can be retrieved."""
    cache.store("key1", {"answer": "hello"})
    result = cache.lookup("key1")
    assert result is not None
    assert result["answer"] == "hello"


def test_lookup_miss_returns_none(
    cache: QueryResultCache,
) -> None:
    """Missing key returns None."""
    assert cache.lookup("absent") is None


def test_lru_eviction(
    cache: QueryResultCache,
) -> None:
    """Oldest entry is evicted at capacity."""
    for i in range(5):
        cache.store(
            f"k{i}",
            {"value": i},
        )
    assert cache.lookup("k0") is None
    assert cache.lookup("k4") is not None


def test_access_promotes_entry(
    cache: QueryResultCache,
) -> None:
    """Accessing an entry prevents eviction."""
    for i in range(4):
        cache.store(f"k{i}", {"v": i})
    cache.lookup("k0")
    cache.store("k4", {"v": 4})
    assert cache.lookup("k0") is not None
    assert cache.lookup("k1") is None


def test_current_size(
    cache: QueryResultCache,
) -> None:
    """Size reflects number of entries."""
    assert cache.current_size() == 0
    cache.store("a", {"x": 1})
    cache.store("b", {"x": 2})
    assert cache.current_size() == 2


def test_overwrite_existing_key(
    cache: QueryResultCache,
) -> None:
    """Storing same key updates the value."""
    cache.store("k", {"old": True})
    cache.store("k", {"new": True})
    result = cache.lookup("k")
    assert result is not None
    assert result.get("new") is True
    assert cache.current_size() == 1


def test_capacity_of_one() -> None:
    """Cache with capacity one works correctly."""
    tiny = QueryResultCache(capacity=1)
    tiny.store("a", {"v": 1})
    tiny.store("b", {"v": 2})
    assert tiny.lookup("a") is None
    assert tiny.lookup("b") is not None


def test_zero_capacity_becomes_one() -> None:
    """Zero capacity is coerced to one."""
    c = QueryResultCache(capacity=0)
    c.store("x", {"v": 1})
    assert c.current_size() == 1
