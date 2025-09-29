import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.resilience.retry_handler import RetryHandler
from backend.resilience.fallback_chain import FallbackChain
from backend.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitBreakerState
from backend.resilience.recitation_handler import RecitationHandler

# --- Existing Tests ---
# (Tests for RetryHandler, FallbackChain, and CircuitBreaker are kept)
@pytest.mark.asyncio
async def test_retry_handler_success_on_first_attempt():
    async_operation = AsyncMock(return_value="success")
    retry_handler = RetryHandler(max_attempts=3)
    result = await retry_handler.execute_with_retry(async_operation)
    async_operation.assert_awaited_once()

@pytest.mark.asyncio
async def test_fallback_chain_success_on_first_model():
    async_operation = AsyncMock(return_value="success_model_1")
    model_list = ["model-1", "model-2"]
    fallback_chain = FallbackChain(models=model_list)
    result, _ = await fallback_chain.execute_with_fallback(async_operation)
    assert result == "success_model_1"
    async_operation.assert_awaited_once()

@pytest.mark.asyncio
async def test_circuit_breaker_starts_closed():
    breaker = CircuitBreaker()
    assert breaker.state == CircuitBreakerState.CLOSED

# --- New Tests for RecitationHandler ---

@pytest.fixture
def recitation_handler():
    """Provides a RecitationHandler instance for testing."""
    return RecitationHandler()

@pytest.mark.parametrize("error_message, expected", [
    ("Response was filtered due to recitation.", True),
    ("Content policy violation: refused to answer.", True),
    ("This content is blocked by the safety filter.", True),
    ("Copyright infringement detected.", True),
    ("An unknown error occurred.", False),
    ("Connection timed out.", False),
    ("", False),
    (None, False),
])
def test_is_recitation_error(recitation_handler, error_message, expected):
    """
    Tests the is_recitation_error method with various error messages.
    """
    assert recitation_handler.is_recitation_error(error_message) == expected

@pytest.mark.parametrize("error_message, expected_category", [
    ("Response was filtered due to recitation.", "recitation"),
    ("The model's response was blocked.", "recitation"),
    ("Exceeded maximum token limit.", "token_limit"),
    ("max_tokens parameter is too low.", "token_limit"),
    ("A network connection timeout occurred.", "connection"),
    ("API server returned a 503 error.", "connection"),
    ("Invalid API key.", "other"),
    ("An unexpected null pointer was found.", "other"),
    ("", "unknown"),
])
def test_categorize_error(recitation_handler, error_message, expected_category):
    """
    Tests the categorize_error method to ensure correct classification of errors.
    """
    assert recitation_handler.categorize_error(error_message) == expected_category