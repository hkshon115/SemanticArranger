"""
This module provides robust retry mechanisms for handling transient network
errors when making API calls.

It includes a `RetryConfig` class for configuration and uses the `tenacity`
library if available, otherwise falling back to a simple custom implementation.
"""
import requests
import time
import random
import asyncio
from functools import wraps
import aiohttp

# Try to import tenacity with correct names
try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
        before_sleep_log,
        RetryError
    )
    import logging
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

# Setup logging for retry messages
if TENACITY_AVAILABLE:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)

class SimpleRetry:
    """Simple exponential backoff retry mechanism when tenacity is not available."""
    
    @staticmethod
    def retry_with_backoff(func, max_attempts=5, base_delay=1.0, max_delay=60.0, 
                          exponential_base=2, jitter=True):
        """
        Retry a function with exponential backoff.
        """
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except (requests.exceptions.Timeout, 
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError) as e:
                last_exception = e
                
                if isinstance(e, requests.exceptions.HTTPError):
                    if e.response.status_code == 429:
                        print(f"⚠️ Rate limited. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                    elif e.response.status_code >= 500:
                        print(f"⚠️ Server error. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                    elif 400 <= e.response.status_code < 500:
                        raise
                else:
                    print(f"⚠️ Connection error. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                
                if attempt < max_attempts - 1:
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    print(f"   Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
        
        raise last_exception

    @staticmethod
    def async_retry_with_backoff(max_attempts=5, base_delay=1.0, max_delay=60.0, 
                                 exponential_base=2, jitter=True):
        """
        A decorator for retrying an async function with exponential backoff.
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except (requests.exceptions.Timeout, 
                            requests.exceptions.ConnectionError,
                            requests.exceptions.HTTPError,
                            aiohttp.ClientResponseError) as e:
                        last_exception = e
                        
                        if isinstance(e, requests.exceptions.HTTPError):
                            if e.response.status_code == 429:
                                print(f"⚠️ Rate limited. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                            elif e.response.status_code >= 500:
                                print(f"⚠️ Server error. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                            elif 400 <= e.response.status_code < 500:
                                raise
                        elif isinstance(e, aiohttp.ClientResponseError):
                            if e.status == 429:
                                print(f"⚠️ Rate limited. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                            elif e.status >= 500:
                                print(f"⚠️ Server error. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                            elif 400 <= e.status < 500:
                                raise
                        else:
                            print(f"⚠️ Connection error. Retrying... (Attempt {attempt + 1}/{max_attempts})")
                        
                        if attempt < max_attempts - 1:
                            delay = min(base_delay * (exponential_base ** attempt), max_delay)
                            
                            if jitter:
                                delay = delay * (0.5 + random.random())
                            
                            print(f"   Waiting {delay:.1f} seconds before retry...")
                            await asyncio.sleep(delay)
                
                raise last_exception
            return wrapper
        return decorator

class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(self, max_attempts=5, min_wait=1, max_wait=60, exponential_base=2):
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.exponential_base = exponential_base
