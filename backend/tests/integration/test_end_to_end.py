import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from backend.processing.orchestrator import PipelineOrchestrator
from backend.config.pipeline_config import PipelineConfig

@pytest.fixture
def golden_pdf_path():
    """Returns the path to a golden test PDF."""
    return os.path.join(os.path.dirname(__file__), "..", "fixtures", "golden_pdfs", "sample_report.pdf")

@pytest.mark.asyncio
@patch('backend.processing.orchestrator.Summarizer')
@patch('backend.processing.orchestrator.Chunker')
@patch('backend.processing.orchestrator.ParallelProcessor')
@patch('backend.processing.orchestrator.ResultMerger')
@patch('backend.processing.orchestrator.AsyncExtractor')
@patch('backend.processing.orchestrator.AsyncRouter')
@patch('backend.processing.orchestrator.AsyncLLMClient')
async def test_end_to_end_pipeline_with_mocked_llm(
    mock_llm_client, mock_router, mock_extractor, mock_merger,
    mock_parallel_processor, mock_chunker, mock_summarizer, golden_pdf_path
):
    """
    Tests the full pipeline end-to-end with a real PDF and mocked LLM calls.
    """
    # --- Configure Mock Instances ---
    mock_extraction_results = [{"page": 1, "content": "text"}]
    mock_summary = {"executive_summary": "summary"}
    mock_chunks = [{"chunk": 1, "content": "text"}]

    # Configure the return_value of the class mocks to be instances
    mock_router_instance = AsyncMock()
    mock_router.return_value = mock_router_instance

    mock_extractor_instance = AsyncMock()
    mock_extractor.return_value = mock_extractor_instance

    mock_parallel_processor_instance = AsyncMock()
    mock_parallel_processor.return_value = mock_parallel_processor_instance
    mock_parallel_processor_instance.process_document.return_value = mock_extraction_results
    
    mock_chunker_instance = MagicMock()
    mock_chunker.return_value = mock_chunker_instance
    mock_chunker_instance.chunk_extraction_result.return_value = mock_chunks
    mock_chunker_instance.get_chunking_stats.return_value = {"total_chunks": 1}

    mock_summarizer_instance = AsyncMock()
    mock_summarizer.return_value = mock_summarizer_instance
    mock_summarizer_instance.generate_summary.return_value = mock_summary

    # --- Run Pipeline ---
    with patch('backend.utils.document_parser.fitz.open') as mock_fitz_open:
        mock_page = MagicMock()
        mock_page.get_text.return_value = "dummy text"
        mock_page.get_pixmap.return_value.tobytes.return_value = b"dummy image bytes"
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        orchestrator = PipelineOrchestrator(api_key="fake_key")
        config = PipelineConfig(concurrency_limit=1)
        result = await orchestrator.process_document_async(golden_pdf_path, config)

    # --- Assertions ---
    assert result["extraction_results"] == mock_extraction_results
    assert result["executive_summary"] == mock_summary
    assert result["chunks"] == mock_chunks
    
    mock_parallel_processor_instance.process_document.assert_awaited_once()
    mock_summarizer_instance.generate_summary.assert_awaited_once()
    mock_chunker_instance.chunk_extraction_result.assert_called_once()
