"""
This module provides a sophisticated error handling and analysis system for
LLM API responses.

It defines a structured `LLMError` class and an `LLMErrorAnalyzer` that can
inspect raw API responses, categorize the type and severity of errors, and
provide user-friendly messages and suggestions for remediation. This allows the
application to respond intelligently to different failure modes, such as
rate limits, content filtering, and malformed responses.
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum
import json
import re
from datetime import datetime

ERROR_HANDLER_AVAILABLE = True

ERROR_HANDLER_AVAILABLE = True

ERROR_HANDLER_AVAILABLE = True


class ErrorType(Enum):
    """Categorization of different LLM error types"""
    # Response errors
    NO_CONTENT = "no_content"
    EMPTY_RESPONSE = "empty_response"
    EMPTY_PARTS = "empty_parts"
    MALFORMED_RESPONSE = "malformed_response"
    
    # Content errors
    PARSING_ERROR = "parsing_error"
    JSON_DECODE_ERROR = "json_decode_error"
    TRUNCATED_RESPONSE = "truncated_response"
    
    # API limits
    TOKEN_LIMIT = "token_limit"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    
    # Safety and filters
    SAFETY_BLOCKED = "safety_blocked"
    CONTENT_FILTERED = "content_filtered"
    
    # Connection errors
    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    API_ERROR = "api_error"
    
    # Unknown
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"        # Can retry with same strategy
    MEDIUM = "medium"  # Should retry with different strategy
    HIGH = "high"      # Should not retry
    CRITICAL = "critical"  # System error


class LLMError:
    """Structured error information for LLM responses"""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_suggested: bool = True,
        suggestions: Optional[List[str]] = None
    ):
        self.type = error_type
        self.message = message
        self.details = details or {}
        self.severity = severity
        self.retry_suggested = retry_suggested
        self.suggestions = suggestions or []
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error_type": self.type.value,
            "error_message": self.message,
            "error_details": self.details,
            "severity": self.severity.value,
            "retry_suggested": self.retry_suggested,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp,
            "user_friendly_message": self.get_user_friendly_message()
        }
    
    def get_user_friendly_message(self) -> str:
        """Get a user-friendly error message"""
        messages = {
            ErrorType.NO_CONTENT: "The model returned no content. This may be due to content complexity or safety filters.",
            ErrorType.EMPTY_RESPONSE: "Received an empty response from the model.",
            ErrorType.EMPTY_PARTS: "The response structure is missing content parts.",
            ErrorType.TOKEN_LIMIT: "Response exceeded token limits. Try reducing input size.",
            ErrorType.RATE_LIMIT: "API rate limit reached. Please wait before retrying.",
            ErrorType.SAFETY_BLOCKED: "Content was blocked by safety filters.",
            ErrorType.TIMEOUT: "Request timed out. The content may be too complex.",
            ErrorType.JSON_DECODE_ERROR: "Failed to parse the model's response as JSON.",
            ErrorType.TRUNCATED_RESPONSE: "The response appears to be incomplete.",
            ErrorType.CONNECTION_ERROR: "Network connection error. Please check your connection.",
            ErrorType.QUOTA_EXCEEDED: "API quota exceeded. Please check your usage limits.",
            ErrorType.CONTENT_FILTERED: "Some content was filtered out by the model.",
            ErrorType.MALFORMED_RESPONSE: "The response format is unexpected.",
            ErrorType.PARSING_ERROR: "Failed to parse the response content.",
            ErrorType.API_ERROR: "An API error occurred.",
            ErrorType.UNKNOWN: "An unknown error occurred."
        }
        return messages.get(self.type, self.message)
    
    def __str__(self) -> str:
        return f"LLMError({self.type.value}): {self.message}"


class LLMErrorAnalyzer:
    """Analyzes LLM responses and extracts detailed error information"""
    
    @staticmethod
    def analyze_gemini_response(response: Dict[str, Any]) -> Optional[LLMError]:
        """Analyze a Gemini API response for errors"""
        
        # Check if it's an error response
        if response.get('error'):
            return LLMErrorAnalyzer._analyze_api_error(response)
        
        # Check candidates
        candidates = response.get('candidates', [])
        if not candidates:
            return LLMError(
                ErrorType.EMPTY_RESPONSE,
                "No candidates in response",
                details={"response_keys": list(response.keys())},
                severity=ErrorSeverity.HIGH,
                suggestions=["Check if the input content is valid", "Try a simpler prompt"]
            )
        
        # Analyze first candidate
        candidate = candidates[0]
        return LLMErrorAnalyzer._analyze_candidate(candidate, response)
    
    @staticmethod
    def _analyze_candidate(candidate: Dict[str, Any], full_response: Dict[str, Any]) -> Optional[LLMError]:
        """Analyze a single candidate for errors"""
        
        # Check finish reason
        finish_reason = candidate.get('finishReason', '')
        if finish_reason:
            error = LLMErrorAnalyzer._analyze_finish_reason(finish_reason, candidate)
            if error:
                return error
        
        # Check content structure
        content = candidate.get('content', {})
        if not content:
            return LLMError(
                ErrorType.NO_CONTENT,
                "Candidate has no content field",
                details={
                    "candidate_keys": list(candidate.keys()),
                    "finish_reason": finish_reason
                },
                severity=ErrorSeverity.HIGH,
                suggestions=["Check content safety", "Simplify the input"]
            )
        
        # Check parts
        parts = content.get('parts', [])
        if not parts:
            return LLMError(
                ErrorType.EMPTY_PARTS,
                "Content has no parts",
                details={
                    "content_keys": list(content.keys()),
                    "role": content.get('role', 'unknown')
                },
                severity=ErrorSeverity.MEDIUM,
                suggestions=["Try a different prompt structure", "Check input image quality"]
            )
        
        # Check if parts have content
        has_text = any(part.get('text') for part in parts)
        if not has_text:
            return LLMError(
                ErrorType.NO_CONTENT,
                "No text content in parts",
                details={
                    "parts_count": len(parts),
                    "part_types": [list(part.keys()) for part in parts]
                },
                severity=ErrorSeverity.MEDIUM,
                suggestions=["Verify the model can process this content type"]
            )
        
        return None  # No error detected
    
    @staticmethod
    def _analyze_finish_reason(finish_reason: str, candidate: Dict[str, Any]) -> Optional[LLMError]:
        """Analyze finish reason for specific errors"""
        
        safety_ratings = candidate.get('safetyRatings', [])
        
        if finish_reason == 'SAFETY':
            blocked_categories = [
                rating for rating in safety_ratings 
                if rating.get('blocked', False)
            ]
            return LLMError(
                ErrorType.SAFETY_BLOCKED,
                "Content blocked by safety filters",
                details={
                    "finish_reason": finish_reason,
                    "safety_ratings": safety_ratings,
                    "blocked_categories": blocked_categories
                },
                severity=ErrorSeverity.HIGH,
                retry_suggested=False,
                suggestions=[
                    "Review content for sensitive material",
                    "Try with more general language",
                    "Remove potentially problematic content"
                ]
            )
        
        elif finish_reason == 'MAX_TOKENS':
            return LLMError(
                ErrorType.TOKEN_LIMIT,
                "Response truncated due to token limit",
                details={
                    "finish_reason": finish_reason,
                    "partial_content_available": True
                },
                severity=ErrorSeverity.MEDIUM,
                suggestions=[
                    "Increase max_tokens parameter",
                    "Reduce input content size",
                    "Split content into smaller chunks"
                ]
            )
        
        elif finish_reason == 'RECITATION':
            return LLMError(
                ErrorType.CONTENT_FILTERED,
                "Content filtered due to recitation concerns",
                details={"finish_reason": finish_reason},
                severity=ErrorSeverity.HIGH,
                suggestions=["Rephrase the prompt", "Avoid requesting copyrighted content"]
            )
        
        elif finish_reason in ['OTHER', 'UNSPECIFIED']:
            return LLMError(
                ErrorType.UNKNOWN,
                f"Response ended with reason: {finish_reason}",
                details={
                    "finish_reason": finish_reason,
                    "safety_ratings": safety_ratings
                },
                severity=ErrorSeverity.MEDIUM
            )
        
        return None
    
    @staticmethod
    def _analyze_api_error(response: Dict[str, Any]) -> LLMError:
        """Analyze API-level errors"""
        
        error = response.get('error', {})
        if isinstance(error, str):
            error_message = error
            error_details = {}
        else:
            error_message = error.get('message', 'Unknown API error')
            error_details = error
        
        # Detect error type from message
        error_type = ErrorType.API_ERROR
        severity = ErrorSeverity.HIGH
        retry_suggested = True
        suggestions = []
        
        if 'rate limit' in error_message.lower():
            error_type = ErrorType.RATE_LIMIT
            severity = ErrorSeverity.MEDIUM
            suggestions = ["Wait before retrying", "Implement exponential backoff"]
        elif 'quota' in error_message.lower():
            error_type = ErrorType.QUOTA_EXCEEDED
            severity = ErrorSeverity.CRITICAL
            retry_suggested = False
            suggestions = ["Check API quota", "Upgrade plan if needed"]
        elif 'timeout' in error_message.lower():
            error_type = ErrorType.TIMEOUT
            severity = ErrorSeverity.MEDIUM
            suggestions = ["Reduce content complexity", "Increase timeout duration"]
        elif 'connection' in error_message.lower():
            error_type = ErrorType.CONNECTION_ERROR
            suggestions = ["Check network connection", "Verify API endpoint"]
        
        return LLMError(
            error_type,
            error_message,
            details=error_details,
            severity=severity,
            retry_suggested=retry_suggested,
            suggestions=suggestions
        )
    
    @staticmethod
    def analyze_json_error(json_str: str, error: Exception) -> LLMError:
        """Analyze JSON parsing errors"""
        
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "json_preview": json_str[:500] if json_str else "No content"
        }
        
        # Check if it's truncated
        if json_str:
            open_braces = json_str.count('{') - json_str.count('}')
            open_brackets = json_str.count('[') - json_str.count(']')
            
            if open_braces > 0 or open_brackets > 0:
                return LLMError(
                    ErrorType.TRUNCATED_RESPONSE,
                    "JSON appears to be truncated",
                    details={
                        **details,
                        "open_braces": open_braces,
                        "open_brackets": open_brackets
                    },
                    suggestions=[
                        "Increase max_tokens",
                        "Request smaller chunks of data",
                        "Simplify the extraction requirements"
                    ]
                )
        
        return LLMError(
            ErrorType.JSON_DECODE_ERROR,
            f"Failed to parse JSON: {str(error)}",
            details=details,
            suggestions=[
                "Ensure prompt requests valid JSON",
                "Check for special characters in content",
                "Try a simpler response format"
            ]
        )


def create_error_report(errors: List[LLMError], output_path: str):
    """Create a detailed error report"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("LLM ERROR ANALYSIS REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n\n")
        
        # Summary
        error_types: Dict[str, int] = {}
        for error in errors:
            error_types[error.type.value] = error_types.get(error.type.value, 0) + 1
        
        f.write("ERROR SUMMARY\n")
        f.write("-"*30 + "\n")
        f.write(f"Total errors: {len(errors)}\n\n")
        
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {error_type}: {count}\n")
        
        # Detailed errors
        f.write("\n\nDETAILED ERRORS\n")
        f.write("="*60 + "\n")
        
        for i, error in enumerate(errors, 1):
            f.write(f"\nError #{i}\n")
            f.write("-"*30 + "\n")
            f.write(f"Type: {error.type.value}\n")
            f.write(f"Severity: {error.severity.value}\n")
            f.write(f"Time: {error.timestamp}\n")
            f.write(f"Message: {error.message}\n")
            f.write(f"User-friendly: {error.get_user_friendly_message()}\n")
            
            if error.suggestions:
                f.write("\nSuggestions:\n")
                for suggestion in error.suggestions:
                    f.write(f"  • {suggestion}\n")
            
            if error.details:
                f.write("\nDetails:\n")
                f.write(json.dumps(error.details, indent=2, ensure_ascii=False))
                f.write("\n")
