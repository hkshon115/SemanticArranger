from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class ChunkingProfile(Enum):
    """
    Defines different chunking profiles tailored for various document types.
    This allows the chunker to use optimal settings based on content.
    """
    STANDARD = "standard"
    COMPLEX_TABLES = "complex_tables"
    SIMPLE = "simple"

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

class PipelineConfig(BaseModel):
    """
    Central configuration for the extraction pipeline's operational parameters.
    
    Attributes:
        concurrency_limit: The max number of pages to process in parallel.
        cache_enabled: Enables or disables caching of LLM responses.
        cache_ttl: Time-to-live for cached items in seconds.
        rate_limit_per_minute: Max number of LLM calls per minute.
        retry_max_attempts: Max number of retries for a failed LLM call.
        retry_backoff_base: The base for the exponential backoff delay.
        fallback_to_raw_text: If true, falls back to raw text extraction on failure.
        key_lang: The target language for summaries and insights.
        extraction_primary_model: The primary model for data extraction.
        summarization_model: The default model for summarization.
        iterative_refinement_enabled: Enables the self-correction mechanism.
    """
    concurrency_limit: int = Field(default=5, ge=1, le=20)
    cache_enabled: bool = True
    cache_ttl: int = 3600
    rate_limit_per_minute: int = 60
    retry_max_attempts: int = 3
    retry_backoff_base: float = 2.0
    fallback_to_raw_text: bool = True
    key_lang: str = "en"
    extraction_primary_model: str = "gemini-2.5-flash"
    summarization_model: str = "gemini-2.5-flash"
    iterative_refinement_enabled: bool = False
