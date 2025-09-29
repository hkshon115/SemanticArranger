"""
Unit tests for the Pydantic data models.
"""
import pytest
from pydantic import ValidationError
from backend.models.extraction import (
    ExtractionStrategy,
    ExtractionPlan,
    RouterAnalysis,
    ExtractionResult,
)

def test_extraction_strategy_enum():
    """Tests that the ExtractionStrategy enum has the correct values."""
    assert [e.value for e in ExtractionStrategy] == [
        "minimal",
        "basic",
        "comprehensive",
        "table_focus",
        "table_chunk",
        "text_only",
        "visual_only",
    ]

def test_extraction_plan_valid():
    """Tests a valid ExtractionPlan model."""
    plan = ExtractionPlan(
        step=1,
        description="Extract header",
        strategy=ExtractionStrategy.BASIC,
        max_tokens=4000,
    )
    assert plan.step == 1
    assert plan.strategy == "basic"

@pytest.mark.parametrize(
    "max_tokens, is_valid",
    [(500, False), (999, False), (1000, True), (50000, True), (50001, False)],
)
def test_extraction_plan_token_limits(max_tokens, is_valid):
    """Tests the token limit validation on the ExtractionPlan model."""
    data = {
        "step": 1,
        "description": "Test tokens",
        "strategy": ExtractionStrategy.MINIMAL,
        "max_tokens": max_tokens,
    }
    if is_valid:
        plan = ExtractionPlan(**data)
        assert plan.max_tokens == max_tokens
    else:
        with pytest.raises(ValidationError):
            ExtractionPlan(**data)

def test_router_analysis_valid():
    """Tests a valid RouterAnalysis model."""
    plan = ExtractionPlan(
        step=1,
        description="Extract table",
        strategy=ExtractionStrategy.TABLE_FOCUS,
        max_tokens=10000,
    )
    analysis = RouterAnalysis(
        page_complexity="complex",
        has_dense_table=True,
        extraction_plans=[plan],
        total_estimated_tokens=10000,
    )
    assert analysis.page_complexity == "complex"
    assert len(analysis.extraction_plans) == 1
    assert analysis.extraction_plans[0].strategy == "table_focus"

def test_extraction_result_valid():
    """Tests a valid ExtractionResult model."""
    result = ExtractionResult(
        step=1,
        strategy="basic",
        success=True,
        content={"title": "Test Title"},
        tokens_used=123,
        time_elapsed=1.23,
        model_used="test-model",
    )
    assert result.success is True
    assert result.content["title"] == "Test Title"
    assert result.model_used == "test-model"

def test_extraction_result_failure():
    """Tests a failed ExtractionResult model."""
    result = ExtractionResult(
        step=2,
        strategy="comprehensive",
        success=False,
        error="Model timed out",
    )
    assert result.success is False
    assert result.error == "Model timed out"
    assert result.content is None
