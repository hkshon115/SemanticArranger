import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from backend.processing.parallel_processor import ParallelProcessor
from backend.config.pipeline_config import PipelineConfig
from backend.models.extraction import ExtractionResult, RouterAnalysis, ExtractionPlan, ExtractionStrategy

# Mock dependencies
@pytest.fixture
def mock_router():
    router = MagicMock()
    router.analyze_page = AsyncMock(return_value=RouterAnalysis(
        page_complexity="moderate",
        has_dense_table=False,
        table_info=None,
        text_sections=1,
        visual_elements=0,
        extraction_plans=[
            ExtractionPlan(step=1, description="Initial", strategy=ExtractionStrategy.COMPREHENSIVE, max_tokens=1000)
        ],
        total_estimated_tokens=1000,
        warnings=[]
    ))
    return router

@pytest.fixture
def mock_extractor():
    extractor = MagicMock()
    
    # Simulate the initial extraction finding a table-like text block
    initial_extraction_result = ExtractionResult(
        step=1, strategy="COMPREHENSIVE", success=True,
        content={
            "key_sections": [{"section_id": "abc", "content": "col1 col2\n1 2\n3 4" * 50}]
        },
        error=None, tokens_used=100, time_elapsed=1.0
    )
    
    # Simulate the refined extraction finding a structured table
    refined_extraction_result = ExtractionResult(
        step=2, strategy="TABLE_FOCUS", success=True,
        content={"tables": [{"title": "Refined Table", "rows": [[1, 2], [3, 4]]}]},
        error=None, tokens_used=100, time_elapsed=1.0
    )
    
    extractor.execute_plan = AsyncMock(side_effect=[
        initial_extraction_result, refined_extraction_result
    ])
    return extractor

@pytest.fixture
def mock_merger():
    merger = MagicMock()
    # The merger will be called twice: once for the initial merge, once for the refinement merge.
    # We can use side_effect to return different values for each call if needed,
    # but for this test, we'll just check that the final merge method is called correctly.
    return merger

@pytest.fixture
def mock_rate_limiter():
    limiter = MagicMock()
    limiter.__aenter__ = AsyncMock(return_value=None)
    limiter.__aexit__ = AsyncMock(return_value=None)
    return limiter

@pytest.mark.asyncio
@patch('backend.processing.parallel_processor.RefinementAnalyzer')
async def test_refinement_workflow_integration(mock_analyzer, mock_router, mock_extractor, mock_merger, mock_rate_limiter):
    """
    Integration test to verify the end-to-end refinement workflow.
    """
    # Mock the analyzer to always suggest a refinement
    mock_analyzer.return_value.analyze_for_missed_tables.return_value = MagicMock(should_refine=True, target_section_id="abc")

    processor = ParallelProcessor(
        router=mock_router,
        extractor=mock_extractor,
        merger=mock_merger,
        rate_limiter=mock_rate_limiter
    )
    
    # Mock a single PDF page
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Some text"
    mock_page.get_pixmap.return_value.tobytes.return_value = b"image"

    # Enable the feature flag
    config = PipelineConfig(iterative_refinement_enabled=True)
    
    # Process the page
    await processor._process_single_page(1, mock_page, asyncio.Semaphore(1), config)

    # --- Verification ---
    # 1. Verify the analyzer was called (implicitly tested by the call to merge_refined_results)
    # 2. Verify a secondary extraction was triggered
    assert mock_extractor.execute_plan.call_count == 2
    second_call_args = mock_extractor.execute_plan.call_args_list[1]
    assert second_call_args[0][0].strategy == ExtractionStrategy.TABLE_FOCUS

    # 3. Verify the correct merger method was called
    assert mock_merger.merge_refined_results.call_count == 1
    
    # 4. Verify the process is skipped when the flag is disabled
    mock_extractor.execute_plan.reset_mock()
    mock_merger.merge_refined_results.reset_mock()
    
    config_disabled = PipelineConfig(iterative_refinement_enabled=False)
    await processor._process_single_page(1, mock_page, asyncio.Semaphore(1), config_disabled)
    
    assert mock_extractor.execute_plan.call_count == 1
    assert mock_merger.merge_refined_results.call_count == 0
