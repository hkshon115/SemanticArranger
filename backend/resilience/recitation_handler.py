"""
Resilience patterns: RECITATION/Content Filtering Handler.
"""
from typing import List

class RecitationHandler:
    """
    A handler for categorizing errors related to content filtering.

    This class helps to identify and categorize different types of LLM errors,
    such as those caused by safety policies (recitation), token limits, or
    connection issues. This allows the application to respond to different
    error types in a more nuanced way.
    """

    # Keywords to identify recitation/content filtering errors.
    RECITATION_INDICATORS = [
        "recitation", "filtered out", "content was filtered", "safety",
        "blocked", "copyright", "content policy", "usage policies", "refused",
    ]

    # Keywords to identify connection-related errors.
    CONNECTION_INDICATORS = [
        "connection", "timeout", "network", "retry", "rate limit",
        "server error", "api error", "500", "502", "503", "504",
        "unavailable", "timed out", "connect failed", "read timeout",
        "ssl", "certificate", "refused", "reset", "model_not_found",
        "invalid_model", "unknown model", "400", "404",
    ]

    # Keywords to identify token limit errors.
    TOKEN_LIMIT_INDICATORS = [
        "token", "truncated", "max_tokens", "exceeded", "response exceeded",
    ]

    def is_recitation_error(self, error_msg: str) -> bool:
        """
        Checks if an error message indicates a recitation/content filtering issue.
        """
        if not error_msg:
            return False
        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in self.RECITATION_INDICATORS)

    def categorize_error(self, error_msg: str) -> str:
        """
        Categorizes an error message into 'recitation', 'token_limit',
        'connection', or 'other'.
        """
        if not error_msg:
            return "unknown"

        error_lower = error_msg.lower()

        if any(indicator in error_lower for indicator in self.RECITATION_INDICATORS):
            return "recitation"
        if any(indicator in error_lower for indicator in self.TOKEN_LIMIT_INDICATORS):
            return "token_limit"
        if any(indicator in error_lower for indicator in self.CONNECTION_INDICATORS):
            return "connection"
        
        return "other"
