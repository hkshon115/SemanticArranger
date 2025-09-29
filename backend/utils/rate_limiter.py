"""
This module provides a token bucket rate limiter for asynchronous operations.

The `RateLimiter` is used to control the frequency of API calls to the LLM
provider, ensuring that the application does not exceed its rate limits.
It is designed to be used as an async context manager.
"""
import asyncio
import time
from typing import List, Dict, Any

class RateLimiter:
    """
    A token bucket rate limiter for async operations.
    """

    def __init__(self, rate_limit: int, period: float = 60.0):
        self.rate_limit = rate_limit
        self.period = period
        self.tokens = self.rate_limit
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def _refill(self):
        """Refills the token bucket."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed > self.period:
            self.tokens = self.rate_limit
            self.last_refill = now

    async def acquire(self):
        """Acquires a token from the bucket, waiting if necessary."""
        async with self._lock:
            await self._refill()
            
            while self.tokens <= 0:
                await asyncio.sleep(1)
                await self._refill()
            
            self.tokens -= 1

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass
