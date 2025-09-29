"""
This module centralizes all configuration for the document processing pipeline.

By externalizing configuration from the application logic, we can easily modify
pipeline behavior, LLM settings, and feature flags without changing the core code.

Modules:
- pipeline_config.py: Defines high-level operational settings (e.g., concurrency).
- llm_config.py: Manages LLM model names, providers, and fallback chains.
- prompt_templates.py: Contains all prompts used for interacting with LLMs.
- feature_flags.yaml: Allows for toggling features on and off.
"""
