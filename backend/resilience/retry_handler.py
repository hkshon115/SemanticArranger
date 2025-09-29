"""
Resilience patterns: Retry handler with exponential backoff.
"""
import asyncio
import random
from typing import Callable, Any

class RetryHandler:
    """
    A handler to automatically retry an operation with exponential backoff.

    This is useful for handling transient errors, such as temporary network
    issues or intermittent service unavailability.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_base: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        """
        Initializes the RetryHandler.

        Args:
            max_attempts: The maximum number of times to try the operation.
            backoff_base: The base for the exponential backoff calculation.
            initial_delay: The initial delay in seconds for the first retry.
            max_delay: The maximum delay in seconds between retries.
        """
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.attempts = []

    async def execute_with_retry(
        self, async_operation: Callable[..., Any], *args, **kwargs
    ) -> Any:
        """
        Executes an async operation with retry logic.

        Args:
            async_operation: The async function to execute.
            *args: Positional arguments for the operation.
            **kwargs: Keyword arguments for the operation.

        Returns:
            The result of the async operation.

        Raises:
            Exception: If the operation fails after all retry attempts.
        """
        last_exception = None
        self.attempts = []
        for attempt in range(self.max_attempts):
            try:
                result = await async_operation(*args, **kwargs)
                self.attempts.append({"attempt": attempt + 1, "status": "success"})
                return result
            except Exception as e:
                last_exception = e
                error_info = f"{type(e).__name__}: {str(e)}"
                self.attempts.append({"attempt": attempt + 1, "status": "failure", "error": error_info})

                if attempt == self.max_attempts - 1:
                    print(f"Attempt {attempt + 1}/{self.max_attempts} failed. No more retries left.")
                    raise

                delay = self.initial_delay * (self.backoff_base ** attempt)
                # Add jitter to avoid thundering herd problem
                jitter = delay * random.uniform(0.1, 0.5)
                final_delay = min(delay + jitter, self.max_delay)

                print(f"Attempt {attempt + 1}/{self.max_attempts} failed with {type(e).__name__}. Retrying in {final_delay:.2f} seconds...")
                await asyncio.sleep(final_delay)
        
        # This path should not be reached, but as a fallback
        raise last_exception