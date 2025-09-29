"""
This module manages shared, reusable HTTP client sessions for both synchronous
(`requests`) and asynchronous (`aiohttp`) API calls.

Using shared sessions with connection pooling is a performance best practice,
as it avoids the overhead of establishing a new TCP connection for every
API request.
"""
import requests
import aiohttp
import asyncio

_shared_session = None
_shared_async_session = None
_async_session_lock = asyncio.Lock()

def get_shared_session():
    """Get or create a shared requests session with connection pooling"""
    global _shared_session
    if _shared_session is None:
        _shared_session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=0
        )
        _shared_session.mount('http://', adapter)
        _shared_session.mount('https://', adapter)
    return _shared_session

async def get_shared_async_session():
    """Get or create a shared aiohttp ClientSession with connection pooling"""
    global _shared_async_session
    if _shared_async_session is None:
        async with _async_session_lock:
            if _shared_async_session is None:
                connector = aiohttp.TCPConnector(limit_per_host=10)
                _shared_async_session = aiohttp.ClientSession(connector=connector)
    return _shared_async_session

