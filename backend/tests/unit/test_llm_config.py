import pytest
from unittest.mock import patch, mock_open
from backend.config.llm_config import LLMConfig, ModelConfig, load_llm_config

@pytest.fixture
def mock_llm_yaml():
    """Mocks the LLM config YAML file."""
    yaml_content = """
router_model: "test-router"
extraction_primary_model: "test-extractor"
extraction_secondary_model: "test-extractor"
extraction_tertiary_model: "test-extractor"
extraction_fallback_model: "test-fallback"
summarization_model: "test-summarizer"
models:
  test-router:
    name: "test-router"
    token_limit: 8000
    provider: "test"
  test-extractor:
    name: "test-extractor"
    token_limit: 16000
    provider: "test"
router_fallback_chains:
  test-router: ["test-fallback"]
"""
    return mock_open(read_data=yaml_content)

def test_llm_config_loading(mock_llm_yaml):
    """
    Tests that the LLM configuration is correctly loaded from a YAML file.
    """
    with patch('builtins.open', mock_llm_yaml):
        config = load_llm_config()

    assert isinstance(config, LLMConfig)
    assert config.router_model == "test-router"
    assert "test-extractor" in config.models
    assert config.models["test-extractor"].token_limit == 16000
    assert config.router_fallback_chains["test-router"] == ["test-fallback"]
