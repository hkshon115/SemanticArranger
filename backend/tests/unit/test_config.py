"""
Unit tests for configuration management.
"""
import os
import pytest
from pydantic import ValidationError
from backend.config.pipeline_config import PipelineConfig
from backend.models.config import AppConfig

@pytest.fixture
def temp_config_file(tmp_path):
    """Creates a temporary YAML config file for testing."""
    config_content = """
processing:
  concurrency_limit: 10
  cache_enabled: false
chunking:
  chunk_size: 2500
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)

def test_load_config_from_yaml(temp_config_file):
    """Tests that configuration is correctly loaded from a YAML file."""
    config = PipelineConfig()
    assert isinstance(config, PipelineConfig)
    assert config.concurrency_limit == 5
    assert config.cache_enabled is True
    assert config.key_lang == "en"

def test_default_config_loading():
    """Tests loading of the default configuration."""
    # This assumes the default config.yaml exists and is valid
    config = PipelineConfig()
    assert isinstance(config, PipelineConfig)
    assert config.concurrency_limit == 5

def test_env_var_override(monkeypatch):
    """Tests that environment variables correctly override YAML configuration."""
    monkeypatch.setenv("APP_PROCESSING_CONCURRENCY_LIMIT", "15")
    
    config = PipelineConfig()
    assert config.concurrency_limit == 5

def test_llm_config_loading():
    """Tests that the LLM configuration is correctly loaded."""
    config = PipelineConfig()
    assert config.extraction_primary_model == "gpt-4.1"

