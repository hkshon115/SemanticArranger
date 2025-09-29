"""
This module contains the provider-specific implementations for interacting
with different LLM APIs.

Each provider module implements the `BaseProvider` interface, adapting the
unique request and response formats of a specific API (e.g., Azure OpenAI,
Claude, Gemini) to the standardized format used by the `LLMClient`.
"""
