"""
Unit tests for the AsyncExtractor.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.core.extractor import AsyncExtractor
from backend.models.extraction import ExtractionPlan, ExtractionStrategy, ExtractionResult

# Mock PageData for testing
class MockPageData:
    @property
    def page_number(self) -> int:
        return 1

    def get_text(self) -> str:
        return "This is a test page with some text."

    def get_image(self) -> bytes:
        return b"fake_image_bytes"

@pytest.mark.asyncio
async def test_extractor_execute_plan_success():
    """Tests that the extractor can successfully execute a plan."""
    mock_client = AsyncMock()
    mock_llm_config = MagicMock()
    mock_llm_config.extraction_primary_model = "test-extractor"

    # Mock the LLM response
    mock_response = {
        "content": '{"title": "Test Document", "content": "This is the extracted content."}',
        "usage": {"total_tokens": 150},
    }
    mock_client.chat.return_value = mock_response

    extractor = AsyncExtractor(mock_client, mock_llm_config)
    plan = ExtractionPlan(
        step=1,
        description="Extract title and content",
        strategy=ExtractionStrategy.BASIC,
        max_tokens=2000,
    )
    page_data = MockPageData()
    result = await extractor.execute_plan(plan, page_data)

    assert isinstance(result, ExtractionResult)
    assert result.success is True
    assert result.content["title"] == "Test Document"
    assert result.tokens_used == 150
    assert result.model_used == "test-extractor"

@pytest.mark.asyncio
async def test_extractor_handles_llm_error():
    """Tests that the extractor handles an error from the LLM client."""
    mock_client = AsyncMock()
    mock_llm_config = MagicMock()
    mock_llm_config.extraction_primary_model = "test-extractor"

    # Mock an error response
    mock_client.chat.return_value = {"error": "Model not available"}

    extractor = AsyncExtractor(mock_client, mock_llm_config)
    plan = ExtractionPlan(
        step=1,
        description="Extract data",
        strategy=ExtractionStrategy.MINIMAL,
        max_tokens=1000,
    )
    page_data = MockPageData()
    result = await extractor.execute_plan(plan, page_data)

    assert result.success is False
    assert result.error == "Model not available"

@pytest.mark.asyncio
async def test_extractor_handles_json_parsing_error():
    """Tests that the extractor handles a malformed JSON response from the LLM."""
    mock_client = AsyncMock()
    mock_llm_config = MagicMock()
    mock_llm_config.extraction_primary_model = "test-extractor"

    # Mock a malformed JSON response
    mock_client.chat.return_value = {"content": '{"title": "Test Document", "content": }'}

    extractor = AsyncExtractor(mock_client, mock_llm_config)
    plan = ExtractionPlan(
        step=1,
        description="Extract data",
        strategy=ExtractionStrategy.COMPREHENSIVE,
        max_tokens=4000,
    )
    page_data = MockPageData()
    result = await extractor.execute_plan(plan, page_data)

    assert result.success is False
    assert "Failed to parse JSON" in result.error
