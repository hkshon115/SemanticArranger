import pytest
import time
import os
from backend.utils.cache_manager import DiskCache

@pytest.fixture
def cache(tmp_path):
    """Provides a DiskCache instance for testing."""
    cache_dir = tmp_path / "cache"
    return DiskCache(cache_dir=str(cache_dir))

def test_cache_set_and_get(cache):
    """
    Tests that an item can be set in the cache and then retrieved.
    """
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

def test_cache_get_non_existent_key(cache):
    """
    Tests that getting a non-existent key returns None.
    """
    assert cache.get("non_existent_key") is None

def test_cache_ttl_expiration(cache):
    """
    Tests that a cached item expires after its TTL.
    """
    cache.set("key2", "value2", ttl=1)
    assert cache.get("key2") == "value2"
    time.sleep(1.1)
    assert cache.get("key2") is None

def test_cache_overwrite(cache):
    """
    Tests that setting an existing key overwrites the old value.
    """
    cache.set("key3", "value3")
    cache.set("key3", "new_value")
    assert cache.get("key3") == "new_value"

def test_cache_hit_miss_metrics(cache):
    """
    Tests that the cache correctly tracks hits and misses.
    """
    assert cache.hits == 0
    assert cache.misses == 0

    cache.get("miss1")
    assert cache.misses == 1

    cache.set("hit1", "value")
    cache.get("hit1")
    assert cache.hits == 1
    
    cache.set("ttl_key", "value", ttl=1)
    time.sleep(1.1)
    cache.get("ttl_key")
    assert cache.misses == 2
