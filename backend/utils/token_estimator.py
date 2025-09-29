"""
This module provides a utility for estimating the number of tokens in a text string.

It uses the `tiktoken` library to provide a reasonably accurate token count,
which is crucial for managing LLM context windows and avoiding token limit
errors. The estimator is cached for performance.
"""
import tiktoken
from functools import lru_cache

class TokenEstimator:
    """
    A utility for estimating the number of tokens in a text string.
    """

    def __init__(self, model_name: str = "gpt-4"):
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except KeyError:
            print(f"Warning: No tokenizer found for model '{model_name}'. Using cl100k_base as a fallback.")
            self.encoder = tiktoken.get_encoding("cl100k_base")

    @lru_cache(maxsize=128)
    def estimate_tokens(self, text: str) -> int:
        """
        Estimates the number of tokens in a text string.
        """
        if not isinstance(text, str):
            return 0
        return len(self.encoder.encode(text))

# Global instance for easy use
default_estimator = TokenEstimator()

def estimate_tokens(text: str) -> int:
    """
    A convenience function that uses the default token estimator.
    """
    return default_estimator.estimate_tokens(text)