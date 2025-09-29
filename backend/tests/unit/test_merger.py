import pytest
from backend.core.merger import ResultMerger
from backend.models.extraction import ExtractionResult

@pytest.fixture
def merger():
    return ResultMerger()

@pytest.fixture
def initial_result():
    return {
        "key_sections": [
            {"section_id": "123", "content": "This is a table..."},
            {"section_id": "456", "content": "This is regular text."}
        ],
        "tables": []
    }

@pytest.fixture
def refined_result_success():
    return ExtractionResult(
        step=2,
        strategy="TABLE_FOCUS",
        success=True,
        content={"tables": [{"title": "New Table", "rows": [[1, 2], [3, 4]]}]},
        error=None,
        tokens_used=100,
        time_elapsed=1.0
    )

@pytest.fixture
def refined_result_failure():
    return ExtractionResult(
        step=2,
        strategy="TABLE_FOCUS",
        success=False,
        content=None,
        error="Extraction failed",
        tokens_used=0,
        time_elapsed=1.0
    )

def test_merge_refined_results_success(merger, initial_result, refined_result_success):
    """
    Tests that the merger correctly adds a new table and removes the old text block.
    """
    merged = merger.merge_refined_results(
        initial_result, refined_result_success, "123"
    )
    
    assert len(merged["tables"]) == 1
    assert merged["tables"][0]["title"] == "New Table"
    assert len(merged["key_sections"]) == 1
    assert merged["key_sections"][0]["section_id"] == "456"

def test_merge_refined_results_failure(merger, initial_result, refined_result_failure):
    """
    Tests that the merger returns the original result if the refined extraction failed.
    """
    merged = merger.merge_refined_results(
        initial_result, refined_result_failure, "123"
    )

    assert len(merged["tables"]) == 0
    assert len(merged["key_sections"]) == 2
    assert merged == initial_result

def test_merge_refined_results_no_table_in_content(merger, initial_result, refined_result_success):
    """
    Tests that the merger returns the original result if the refined extraction
    succeeded but did not produce any tables.
    """
    refined_result_success.content = {"key_sections": [{"content": "some text"}]}
    merged = merger.merge_refined_results(
        initial_result, refined_result_success, "123"
    )

    assert len(merged["tables"]) == 0
    assert len(merged["key_sections"]) == 2
    assert merged == initial_result