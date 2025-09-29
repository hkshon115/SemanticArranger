"""
This module provides a client for interacting with various Large Language Models (LLMs).

It abstracts the complexities of different LLM provider APIs into a unified,
provider-agnostic client, available in both synchronous and asynchronous versions.

Modules:
- async_client.py: An asynchronous client for non-blocking LLM calls.
- client.py: A synchronous client for standard, blocking LLM calls.
- providers/: Contains the specific implementations for each LLM provider.
- utils/: Shared utilities for the LLM clients, such as retry logic.
- error_handler.py: A sophisticated handler for categorizing and analyzing LLM errors.
"""
