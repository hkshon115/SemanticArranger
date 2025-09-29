"""
Resilience patterns: Model fallback chain.
"""
import asyncio
from typing import Callable, Any, List, Dict, Tuple

class FallbackChain:
    """
    A handler to execute an operation with a chain of models, falling back
    to the next model in the chain if the previous one fails. This is useful
    for ensuring that a critical operation succeeds even if the primary
    model is unavailable or fails.
    """

    def __init__(self, models: List[str]):
        """
        Initializes the FallbackChain.

        Args:
            models: A list of model names in the order they should be tried.
        """
        if not models:
            raise ValueError("Model list cannot be empty.")
        self.models = models
        self.attempts = []

    async def execute_with_fallback(
        self, async_operation: Callable[..., Any], **kwargs
    ) -> Tuple[Any, List[Dict]]:
        """
        Executes an async operation with a model fallback chain.

        The `async_operation` is expected to accept a 'model' keyword argument.

        Args:
            async_operation: The async function to execute.
            **kwargs: Keyword arguments for the operation.

        Returns:
            A tuple containing the result of the successful operation and a
            list of attempt statistics.

        Raises:
            Exception: If the operation fails for all models in the chain.
        """
        last_exception = None
        self.attempts = []

        for model in self.models:
            try:
                # Pass the current model to the operation
                result = await async_operation(model=model, **kwargs)
                
                # Record successful attempt
                self.attempts.append({"model": model, "status": "success"})
                
                # Return the result of the first successful operation
                return result, self.attempts
            except Exception as e:
                last_exception = e
                
                # Record failed attempt
                error_info = f"{type(e).__name__}: {str(e)}"
                self.attempts.append({"model": model, "status": "failure", "error": error_info})
                
                print(f"Operation failed with model '{model}': {error_info}. Trying next model...")
                # Optional: add a small delay before trying the next model
                await asyncio.sleep(0.2)

        # If all models in the chain fail, raise the last exception
        print(f"All models in the fallback chain failed. Last error: {last_exception}")
        raise last_exception