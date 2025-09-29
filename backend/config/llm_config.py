"""
Centralized configuration for LLM models, including names, token limits,
and fallback chains.
"""
import yaml
from pydantic import BaseModel, Field
from typing import List, Dict

class ModelConfig(BaseModel):
    """
    Configuration for a single LLM, including its provider and token limit.
    
    Attributes:
        name: The unique identifier for the model.
        token_limit: The maximum number of tokens the model can handle.
        provider: The API provider for the model (e.g., 'openai', 'google').
    """
    name: str
    token_limit: int = Field(..., ge=1000)
    provider: str

class LLMConfig(BaseModel):
    """
    Root model for all LLM configurations. It defines the default models for
    different pipeline tasks and contains a dictionary of all available models.
    
    Attributes:
        router_model: The default model for the content routing task.
        extraction_primary_model: The primary model for data extraction.
        extraction_secondary_model: The secondary model for data extraction.
        extraction_tertiary_model: The tertiary model for data extraction.
        extraction_fallback_model: The final fallback model for data extraction.
        summarization_model: The default model for summarization.
        models: A dictionary mapping model names to their ModelConfig.
        router_fallback_chains: Defines the fallback sequence if the primary router fails.
    """
    router_model: str
    extraction_primary_model: str
    extraction_secondary_model: str
    extraction_tertiary_model: str
    extraction_fallback_model: str
    summarization_model: str
    
    models: Dict[str, ModelConfig]
    router_fallback_chains: Dict[str, List[str]]

def load_llm_config(path: str = "backend/config/llm_config.yaml") -> LLMConfig:
    """Loads the LLM configuration from a YAML file."""
    with open(path, "r") as f:
        config_data = yaml.safe_load(f)
    return LLMConfig(**config_data)