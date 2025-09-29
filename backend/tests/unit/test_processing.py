import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from backend.processing.chunker import Chunker
from backend.config.pipeline_config import ChunkingProfile, PipelineConfig
from backend.processing.summarizer import Summarizer

# --- Existing Tests for ParallelProcessor ---
# (Keeping them to ensure the test file remains valid)
def test_parallel_processor_placeholder():
    assert True

# --- New Tests for Chunker ---

@pytest.fixture
def chunker():
    """Provides a Chunker instance for testing."""
    return Chunker(key_lang="en")

def test_chunker_with_valid_data(chunker):
    """
    Tests that the chunker correctly processes a list of valid extraction results.
    """
    extraction_results = [
        {
            "main_title": "Page 1 Title",
            "page_summary": "This is a summary of page 1.",
            "key_sections": [{"section_title": "Section 1", "content": "Some text."}],
            "page_complexity": "simple",
        }
    ]
    chunks = chunker.chunk_extraction_result(extraction_results)
    
    assert len(chunks) == 1
    assert "Page 1 Title" in chunks[0]["page_content"]
    assert chunks[0]["metadata"]["chunking_profile"] == ChunkingProfile.SIMPLE.value
    assert chunker.get_chunking_stats()["total_chunks"] == 1

def test_chunker_with_empty_data(chunker):
    """
    Tests that the chunker returns an empty list when given no extraction results.
    """
    chunks = chunker.chunk_extraction_result([])
    assert len(chunks) == 0
    assert chunker.get_chunking_stats()["total_chunks"] == 0

def test_chunker_skips_invalid_pages(chunker):
    """
    Tests that the chunker skips pages that fail validation (e.g., no content).
    """
    extraction_results = [
        {"main_title": "Valid Page"},
        {"page_summary": None, "key_sections": []}, # Invalid page
    ]
    chunks = chunker.chunk_extraction_result(extraction_results)
    
    assert len(chunks) == 1
    stats = chunker.get_chunking_stats()
    assert stats["total_chunks"] == 1
    assert stats["empty_pages"] == 1

def test_chunker_3000_token_optimization(chunker):
    """
    Tests that content under the 3000-token limit remains in a single chunk.
    """
    long_text = " ".join(["word"] * 2000) # Approx. 2000 tokens
    extraction_results = [
        {
            "main_title": "Long Page",
            "page_summary": "Summary.",
            "key_sections": [{"section_title": "Main", "content": long_text}],
        }
    ]
    chunks = chunker.chunk_extraction_result(extraction_results)
    
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["is_full_page"] is True

def test_chunker_splits_large_pages(chunker):
    """
    Tests that content exceeding the 3000-token limit is split into multiple chunks.
    """
    # This text will be well over the 3000 token limit for the standard profile
    long_text = " ".join(["word"] * 10000)
    extraction_results = [
        {
            "main_title": "Very Long Page",
            "page_summary": "Summary.",
            "key_sections": [{"section_title": "Main", "content": long_text}],
        }
    ]
    chunks = chunker.chunk_extraction_result(extraction_results)
    
    assert len(chunks) > 1
    assert chunks[0]["metadata"]["is_full_page"] is False
    assert chunks[0]["metadata"]["total_chunks"] > 1

# --- New Tests for Summarizer ---

@pytest.fixture
def mock_llm_client():
    """Provides a mock AsyncLLMClient."""
    return AsyncMock()

@pytest.fixture
def summarizer(mock_llm_client):
    """Provides a Summarizer instance with a mock client."""
    return Summarizer(client=mock_llm_client)

@pytest.mark.asyncio
async def test_summarizer_generate_summary_success(summarizer, mock_llm_client):
    """
    Tests that the summarizer successfully generates a summary from extraction results.
    """
    extraction_results = [
        {"main_title": "Page 1", "page_summary": "Summary 1."},
        {"main_title": "Page 2", "page_summary": "Summary 2."},
    ]
    config = PipelineConfig(summarization_model="test-summarizer")
    
    # Configure the mock client to return a valid JSON response
    mock_llm_client.chat.return_value = {
        "content": '{"executive_summary": "Global summary.", "key_takeaways": [], "document_metadata": {}}'
    }

    summary = await summarizer.generate_summary(extraction_results, config)

    assert summary["executive_summary"] == "Global summary."
    assert "fallback_used" not in summary["metadata"]
    mock_llm_client.chat.assert_awaited_once()

@pytest.mark.asyncio
async def test_summarizer_fallback_on_llm_error(summarizer, mock_llm_client):
    """
    Tests that the summarizer returns a fallback summary when the LLM call returns an error.
    """
    extraction_results = [{"page_summary": "A summary."}]
    config = PipelineConfig()

    # Configure the mock client to return an error
    mock_llm_client.chat.return_value = {"error": "LLM service unavailable"}

    summary = await summarizer.generate_summary(extraction_results, config)

    assert summary["executive_summary"] == "Summary generation failed."
    assert summary["metadata"]["fallback_used"] is True
    assert "LLM service unavailable" in summary["metadata"]["error"]

@pytest.mark.asyncio
async def test_summarizer_fallback_on_json_parse_error(summarizer, mock_llm_client):
    """
    Tests that the summarizer returns a fallback summary when the LLM response is not valid JSON.
    """
    extraction_results = [{"page_summary": "A summary."}]
    config = PipelineConfig()

    # Configure the mock client to return invalid JSON
    mock_llm_client.chat.return_value = {"content": "This is not JSON."}

    summary = await summarizer.generate_summary(extraction_results, config)

    assert summary["executive_summary"] == "Summary generation failed."
    assert summary["metadata"]["fallback_used"] is True
    assert "Failed to parse JSON" in summary["metadata"]["error"]
