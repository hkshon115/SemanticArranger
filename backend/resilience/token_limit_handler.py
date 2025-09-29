"""
Resilience pattern: Handler for automatically retrying an operation
with an increased token limit upon a specific failure.
"""
import asyncio
from typing import Callable, Any, Dict

# Error categorization logic (ported from RecitationHandler for self-containment)
TOKEN_LIMIT_INDICATORS = [
    "token", "truncated", "max_tokens", "exceeded", "response exceeded", "maximum context length"
]

def categorize_error(error_msg: str) -> str:
    """Categorizes an error message into 'token_limit' or 'other'."""
    if not error_msg:
        return "unknown"
    error_lower = error_msg.lower()
    if any(indicator in error_lower for indicator in TOKEN_LIMIT_INDICATORS):
        return "token_limit"
    return "other"

class TokenLimitHandler:
    """
    A handler to automatically retry an LLM operation with an increased
    token limit if it fails due to a token-related error. This is a simple
    but effective way to handle cases where the initial token allocation was
    insufficient.
    """

    def __init__(self, token_boost_value: int = 100000):
        """
        Initializes the TokenLimitHandler.

        Args:
            token_boost_value: The new `max_tokens` value to use for the retry.
        """
        self.token_boost_value = token_boost_value

    async def execute_with_token_retry(
        self, async_operation: Callable[..., Any], **kwargs
    ) -> Any:
        """
        Executes an async operation, retrying with more tokens on failure.

        This method specifically checks for errors indicating a token limit
        was exceeded. If such an error is found, it retries the operation once
        with a significantly higher token limit.

        Args:
            async_operation: The async function to execute (e.g., client.chat).
            **kwargs: Keyword arguments for the operation, which must include
                      'max_tokens'.

        Returns:
            The result of the async operation.

        Raises:
            Exception: If the operation fails for a non-token-limit reason,
                         or if it fails again after the retry.
        """
        original_tokens = kwargs.get("max_tokens", 4000)

        try:
            # First attempt with original tokens
            return await async_operation(**kwargs)
        except Exception as e:
            error_msg = str(e)
            error_category = categorize_error(error_msg)

            if error_category == "token_limit":
                print(f"   Token limit error detected. Retrying with boosted token limit.")
                
                # Modify kwargs for the retry
                kwargs["max_tokens"] = self.token_boost_value
                
                # Second and final attempt
                return await async_operation(**kwargs)
            else:
                # If it's not a token limit error, just re-raise it
                raise e
