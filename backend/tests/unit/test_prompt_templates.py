"""
Unit tests for the prompt template management system.
"""
import pytest
from backend.config.prompt_templates import get_extraction_prompt, ROUTER_ANALYSIS_PROMPT
from backend.models.extraction import ExtractionStrategy

def test_router_analysis_prompt_exists():
    """Tests that the main router analysis prompt is defined."""
    assert ROUTER_ANALYSIS_PROMPT is not None
    assert "You are an expert document analyzer" in ROUTER_ANALYSIS_PROMPT

@pytest.mark.parametrize("strategy", list(ExtractionStrategy))
def test_all_strategies_have_prompts(strategy):
    """Tests that all defined extraction strategies have a corresponding prompt."""
    prompt = get_extraction_prompt(strategy)
    assert prompt is not None
    assert len(prompt) > 0

def test_language_formatting():
    """Tests that the language placeholder is correctly formatted in the prompt."""
    prompt = get_extraction_prompt(ExtractionStrategy.BASIC, key_lang="ko")
    assert "in ko language" in prompt
    assert "TARGET_LANG" not in prompt

def test_special_instructions():
    """Tests that special instructions are correctly prepended to the prompt."""
    instructions = "Focus on the financial data."
    prompt = get_extraction_prompt(ExtractionStrategy.COMPREHENSIVE, special_instructions=instructions)
    assert instructions in prompt

def test_anti_recitation_prompt_selection():
    """Tests that the anti-recitation flag returns a different, specialized prompt."""
    standard_prompt = get_extraction_prompt(ExtractionStrategy.MINIMAL)
    anti_recitation_prompt = get_extraction_prompt(ExtractionStrategy.MINIMAL, anti_recitation=True)
    
    assert standard_prompt != anti_recitation_prompt
    assert "Do NOT copy text verbatim" in anti_recitation_prompt
    assert "Extract all text in its original language" not in anti_recitation_prompt

def test_get_extraction_prompt_returns_minimal_for_unknown_strategy():
    """
    Tests that the function gracefully falls back to the MINIMAL prompt
    if an unknown strategy is somehow passed.
    """
    unknown_strategy = "non_existent_strategy"
    prompt = get_extraction_prompt(unknown_strategy)
    expected_minimal_prompt = get_extraction_prompt(ExtractionStrategy.MINIMAL)
    assert prompt == expected_minimal_prompt
