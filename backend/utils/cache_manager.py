import os
import pickle
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

class Cache(ABC):
    """Abstract base class for a cache."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieves an item from the cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Sets an item in the cache with an optional TTL."""
        pass

class DiskCache(Cache):
    """
    A disk-based cache implementation that stores cached items as pickle files.

    This cache provides a simple way to persist data between runs, which can be
    useful for caching the results of expensive operations like LLM calls.
    It supports time-to-live (TTL) for automatic expiration of cached items.
    """

    def __init__(self, cache_dir: str = ".cache"):
        """
        Initializes the DiskCache.

        Args:
            cache_dir: The directory where cached items will be stored.
        """
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _get_file_path(self, key: str) -> str:
        """Returns the file path for a given cache key."""
        return os.path.join(self.cache_dir, f"{key}.pkl")

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves an item from the cache.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The cached value, or None if the item is not found or has expired.
        """
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            self.misses += 1
            return None

        with open(file_path, "rb") as f:
            data = pickle.load(f)
        
        if time.time() > data["expiry"]:
            os.remove(file_path)
            self.misses += 1
            return None
        
        self.hits += 1
        return data["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = 3600):
        """
        Sets an item in the cache with a TTL.

        Args:
            key: The key of the item to set.
            value: The value to be cached.
            ttl: The time-to-live in seconds. Defaults to 3600 (1 hour).
        """
        file_path = self._get_file_path(key)
        expiry = time.time() + ttl if ttl is not None else float("inf")
        
        with open(file_path, "wb") as f:
            pickle.dump({"value": value, "expiry": expiry}, f)
