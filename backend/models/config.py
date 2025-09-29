"""
Pydantic models for configuration management.
"""
from pydantic import BaseModel, Field
from typing import List

class ProcessingConfig(BaseModel):
    """
    Central configuration for the processing pipeline's operational parameters.
    
    Attributes:
        concurrency_limit: The max number of pages to process in parallel.
        cache_enabled: Enables or disables caching of LLM responses.
        cache_ttl: Time-to-live for cached items in seconds.
        rate_limit_per_minute: Max number of LLM calls per minute.
        retry_max_attempts: Max number of retries for a failed LLM call.
        retry_backoff_base: The base for the exponential backoff delay.
        fallback_to_raw_text: If true, falls back to raw text extraction on failure.
    """
    concurrency_limit: int = Field(default=5, ge=1, le=20)
    cache_enabled: bool = True
    cache_ttl: int = 3600
    rate_limit_per_minute: int = 60
    retry_max_attempts: int = 3
    retry_backoff_base: float = 2.0
    fallback_to_raw_text: bool = True

class ChunkConfig(BaseModel):
    """
    Configuration for the document chunking process.
    
    Attributes:
        chunk_size: The target size for each text chunk in tokens.
        chunk_overlap: The number of tokens to overlap between chunks.
        profile: The chunking profile to use.
        separators: A list of strings to use as separators for splitting text.
    """
    chunk_size: int = 3000
    chunk_overlap: int = 200
    profile: str = "standard"
    separators: List[str] = Field(default_factory=lambda: ["\n\n", "\n", ". ", " ", ""])

from backend.config.llm_config import LLMConfig

class AppConfig(BaseModel):
    """
    Root application configuration model that aggregates all other
    configuration models.
    """
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    chunking: ChunkConfig = Field(default_factory=ChunkConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
