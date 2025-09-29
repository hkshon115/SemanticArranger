"""
This module defines the abstract base class for all LLM providers.

It establishes the contract that all provider-specific implementations must
adhere to, ensuring that the `LLMClient` can interact with them in a
consistent way.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Iterator, List, Union
import requests
from ..utils.retry import RetryConfig, SimpleRetry, TENACITY_AVAILABLE

if TENACITY_AVAILABLE:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
    import logging
    logger = logging.getLogger(__name__)

class BaseProvider(ABC):
    def __init__(self, api_key: str, retry_config: Optional[RetryConfig] = None):
        self.api_key = api_key
        self.retry_config = retry_config or RetryConfig()

    @abstractmethod
    def send_message(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs) -> Iterator[Dict[str, Any]]:
        pass

    def _execute_with_retry(self, func, *args, **kwargs):
        if TENACITY_AVAILABLE:
            @retry(
                stop=stop_after_attempt(self.retry_config.max_attempts),
                wait=wait_exponential(
                    min=self.retry_config.min_wait,
                    max=self.retry_config.max_wait,
                    exp_base=self.retry_config.exponential_base
                ),
                retry=retry_if_exception_type((
                    requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError
                )),
                before_sleep=before_sleep_log(logger, logging.WARNING)
            )
            def _wrapped():
                return func(*args, **kwargs)
            return _wrapped()
        else:
            return SimpleRetry.retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_attempts=self.retry_config.max_attempts
            )

    async def _execute_with_retry_async(self, func, *args, **kwargs):
        if TENACITY_AVAILABLE:
            from tenacity.asyncio import AsyncRetrying
            
            async def _wrapped():
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self.retry_config.max_attempts),
                    wait=wait_exponential(
                        min=self.retry_config.min_wait,
                        max=self.retry_config.max_wait,
                        exp_base=self.retry_config.exponential_base
                    ),
                    retry=retry_if_exception_type((
                        requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError,
                        requests.exceptions.HTTPError
                    )),
                    before_sleep=before_sleep_log(logger, logging.WARNING)
                ):
                    with attempt:
                        return await func(*args, **kwargs)
            return await _wrapped()
        else:
            @SimpleRetry.async_retry_with_backoff(max_attempts=self.retry_config.max_attempts)
            async def _wrapped():
                return await func(*args, **kwargs)
            return await _wrapped()
