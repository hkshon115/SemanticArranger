import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from backend.processing.orchestrator import PipelineOrchestrator
from backend.config.pipeline_config import PipelineConfig

@pytest.mark.asyncio
async def test_pipeline_orchestrator_end_to_end_flow():
    """
    Tests the end-to-end orchestration of the pipeline with mocked components.
    """
    # Mock the dependencies
    with patch('backend.processing.orchestrator.AsyncLLMClient') as mock_client, \
         patch('backend.processing.orchestrator.AsyncRouter') as mock_router, \
         patch('backend.processing.orchestrator.AsyncExtractor') as mock_extractor, \
         patch('backend.processing.orchestrator.ResultMerger') as mock_merger, \
         patch('backend.processing.orchestrator.Chunker') as mock_chunker, \
         patch('backend.processing.orchestrator.Summarizer') as mock_summarizer, \
         patch('backend.processing.orchestrator.ParallelProcessor') as mock_parallel_processor, \
         patch('backend.utils.document_parser.fitz.open') as mock_fitz_open:

        # Configure the mock instances
        mock_client.return_value = AsyncMock()
        mock_router.return_value = AsyncMock()
        mock_extractor.return_value = AsyncMock()
        mock_merger.return_value = MagicMock()
        mock_chunker.return_value = MagicMock()
        mock_summarizer.return_value = AsyncMock()
        mock_parallel_processor.return_value = AsyncMock()

        # Set up the return values for the mocked methods
        mock_extraction_results = [{"page": 1, "content": "text"}]
        mock_summary = {"executive_summary": "summary"}
        mock_chunks = [{"chunk": 1, "content": "text"}]
        
        mock_router.return_value.analyze_page.return_value = MagicMock(extraction_plans=[])
        mock_extractor.return_value.execute_plan.return_value = MagicMock(success=True, content={})
        mock_merger.return_value.merge_results.return_value = {"page": 1, "content": "text"}
        
        mock_parallel_processor.return_value.process_document.return_value = mock_extraction_results
        mock_summarizer.return_value.generate_summary.return_value = mock_summary
        mock_chunker.return_value.chunk_extraction_result.return_value = mock_chunks
        mock_chunker.return_value.get_chunking_stats.return_value = {"total_chunks": 1}

        # Configure the mock for fitz.open
        mock_page = MagicMock()
        mock_page.get_text.return_value = "dummy text"
        mock_page.get_pixmap.return_value.tobytes.return_value = b"dummy image bytes"
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc

        # Initialize the orchestrator
        orchestrator = PipelineOrchestrator(api_key="test_key")
        config = PipelineConfig()

        # Run the pipeline
        result = await orchestrator.process_document_async("dummy.pdf", config)

        # Verify the results
        assert result["extraction_results"] == mock_extraction_results
        assert result["executive_summary"] == mock_summary
        assert result["chunks"] == mock_chunks
        assert result["chunking_stats"]["total_chunks"] == 1

        # Verify that the components were called correctly
        mock_parallel_processor.return_value.process_document.assert_awaited_once_with("dummy.pdf", config)
        mock_summarizer.return_value.generate_summary.assert_awaited_once_with(
            mock_extraction_results, config, summarizer_llm_model=None
        )
        mock_chunker.return_value.chunk_extraction_result.assert_called_once_with(mock_extraction_results)

@pytest.mark.asyncio
async def test_summarizer_model_selection():
    """
    Tests that the summarizer_llm_model is correctly passed to the Summarizer.
    """
    with patch('backend.processing.orchestrator.AsyncLLMClient'), \
         patch('backend.processing.orchestrator.AsyncRouter'), \
         patch('backend.processing.orchestrator.AsyncExtractor'), \
         patch('backend.processing.orchestrator.ResultMerger'), \
         patch('backend.processing.orchestrator.Chunker'), \
         patch('backend.processing.orchestrator.Summarizer') as mock_summarizer, \
         patch('backend.processing.orchestrator.ParallelProcessor') as mock_parallel_processor:

        mock_summarizer.return_value = AsyncMock()
        mock_parallel_processor.return_value = AsyncMock()
        mock_parallel_processor.return_value.process_document.return_value = []

        orchestrator = PipelineOrchestrator(api_key="test_key")
        config = PipelineConfig()
        custom_model = "gpt-4o"

        await orchestrator.process_document_async(
            "dummy.pdf", config, summarizer_llm_model=custom_model
        )

        mock_summarizer.return_value.generate_summary.assert_awaited_once_with(
            [], config, summarizer_llm_model=custom_model
        )
