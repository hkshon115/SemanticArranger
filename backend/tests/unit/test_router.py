import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.core.router import AsyncRouter
from backend.models.extraction import RouterAnalysis
from backend.config.llm_config import LLMConfig
from backend.utils.document_parser import PageData

@pytest.fixture
def mock_llm_client():
    """Provides a mock AsyncLLMClient."""
    return AsyncMock()

@pytest.fixture
def router(mock_llm_client):
    """Provides an AsyncRouter instance with a mock client."""
    llm_config = LLMConfig(
        router_model="test-router",
        extraction_primary_model="test-extractor",
        extraction_secondary_model="test-extractor",
        extraction_tertiary_model="test-extractor",
        extraction_fallback_model="test-fallback",
        summarization_model="test-summarizer",
        models={"test-router": {"name": "test-router", "token_limit": 8000, "provider": "test"}},
        router_fallback_chains={"test-router": ["test-fallback"]},
    )
    return AsyncRouter(client=mock_llm_client, llm_config=llm_config)

@pytest.mark.asyncio
async def test_router_analyze_page_success(router, mock_llm_client):
    """
    Tests that the router successfully analyzes a page and returns a valid plan.
    """
    # Mock PageData
    mock_page_data = MagicMock(spec=PageData)
    mock_page_data.get_image.return_value = b"dummy_image"
    mock_page_data.get_text.return_value = "dummy text"

    # Mock LLM response
    mock_llm_client.chat.return_value = {
        "content": '''
        {
            "page_complexity": "moderate",
            "has_dense_table": false,
            "extraction_plans": [
                {"step": 1, "description": "Extract text", "strategy": "basic", "max_tokens": 2000}
            ],
            "total_estimated_tokens": 2000
        }
        '''
    }

    analysis = await router.analyze_page(mock_page_data, "en")

    assert isinstance(analysis, RouterAnalysis)
    assert analysis.page_complexity == "moderate"
    assert len(analysis.extraction_plans) == 1
    mock_llm_client.chat.assert_awaited_once()

@pytest.mark.asyncio
async def test_router_fallback_plan(router, mock_llm_client):
    """
    Tests that the router returns a fallback plan when the LLM call fails.
    """
    mock_page_data = MagicMock(spec=PageData)
    mock_page_data.get_image.return_value = b"dummy_image"
    mock_page_data.get_text.return_value = "dummy text"

    # Mock LLM failure
    mock_llm_client.chat.return_value = {"error": "LLM failed"}

    analysis = await router.analyze_page(mock_page_data, "en")

    assert isinstance(analysis, RouterAnalysis)
    assert analysis.page_complexity == "unknown"
    assert len(analysis.extraction_plans) > 0
    assert "Router failed" in analysis.warnings[0]