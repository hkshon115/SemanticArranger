import asyncio
import time
from enum import Enum
from typing import Callable, Any

class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenError(Exception):
    """Exception raised when the circuit breaker is open."""
    pass

class CircuitBreaker:
    """
    An async-compatible circuit breaker to prevent repeated calls to a failing service.

    This pattern is used to avoid overwhelming a struggling service with requests.
    If a service fails a certain number of times, the circuit "opens" and further
    calls are blocked for a timeout period. After the timeout, the circuit enters
    a "half-open" state to test if the service has recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30, # seconds
        half_open_attempts: int = 2,
    ):
        """
        Initializes the CircuitBreaker.

        Args:
            failure_threshold: The number of failures required to open the circuit.
            recovery_timeout: The time in seconds to wait before moving to half-open.
            half_open_attempts: The number of successful calls required in the
                                half-open state to close the circuit.
        """
        if failure_threshold < 1:
            raise ValueError("Failure threshold must be at least 1.")
        if recovery_timeout < 1:
            raise ValueError("Recovery timeout must be at least 1 second.")
        
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts
        
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_success_count = 0

    @property
    def state(self) -> CircuitBreakerState:
        """
        Returns the current state of the circuit breaker, transitioning to
        half-open if the recovery timeout has passed.
        """
        if self._state == CircuitBreakerState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self.to_half_open()
        return self._state

    def to_closed(self):
        """Transitions the circuit to the CLOSED state."""
        print("Circuit Breaker: State changed to CLOSED.")
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0

    def to_open(self):
        """Transitions the circuit to the OPEN state."""
        print(f"Circuit Breaker: State changed to OPEN for {self.recovery_timeout} seconds.")
        self._state = CircuitBreakerState.OPEN
        self._last_failure_time = time.monotonic()

    def to_half_open(self):
        """Transitions the circuit to the HALF_OPEN state."""
        print("Circuit Breaker: State changed to HALF_OPEN.")
        self._state = CircuitBreakerState.HALF_OPEN
        self._half_open_success_count = 0

    async def execute(self, async_operation: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Executes an async operation, respecting the circuit breaker's state.

        Args:
            async_operation: The async function to execute.
            *args: Positional arguments for the operation.
            **kwargs: Keyword arguments for the operation.

        Returns:
            The result of the async operation.

        Raises:
            CircuitBreakerOpenError: If the circuit is open.
        """
        if self.state == CircuitBreakerState.OPEN:
            raise CircuitBreakerOpenError("Circuit is open. Operation blocked.")

        try:
            result = await async_operation(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handles the logic for a successful operation call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._half_open_success_count += 1
            if self._half_open_success_count >= self.half_open_attempts:
                self.to_closed()
        else:
            # If it was already closed, reset failure count just in case
            self._failure_count = 0

    def _on_failure(self):
        """Handles the logic for a failed operation call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.to_open()
        else:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self.to_open()
