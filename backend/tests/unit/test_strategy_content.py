import pytest
from unittest.mock import MagicMock
from backend.strategies.minimal import MinimalStrategy
from backend.strategies.basic import BasicStrategy
from backend.strategies.comprehensive import ComprehensiveStrategy
from backend.strategies.visual import VisualStrategy
from backend.strategies.table_chunk import TableChunkStrategy
from backend.strategies.table_focused import TableFocusedStrategy
from backend.strategies.text_only import TextOnlyStrategy
from backend.models.extraction import ExtractionPlan, ExtractionStrategy
from backend.config.pipeline_config import PipelineConfig
from backend.core.interfaces import PageData

@pytest.fixture
def mock_page_data():
    """Fixture for mock page data."""
    page_data = MagicMock(spec=PageData)
    page_data.get_image.return_value = b"test_image_bytes"
    page_data.get_text.return_value = "This is a test page."
    return page_data

@pytest.fixture
def mock_plan():
    """Fixture for a mock extraction plan."""
    return ExtractionPlan(
        step=1,
        description="Test Plan",
        strategy=ExtractionStrategy.MINIMAL,
        max_tokens=1000,
        special_instructions="Test instructions"
    )

@pytest.fixture
def mock_config():
    """Fixture for a mock pipeline config."""
    return PipelineConfig(key_lang="en")

def test_minimal_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of MinimalStrategy."""
    strategy = MinimalStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]

def test_basic_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of BasicStrategy."""
    strategy = BasicStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]
    assert "Text excerpt" in content[0]["text"]

def test_comprehensive_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of ComprehensiveStrategy."""
    strategy = ComprehensiveStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]
    assert "Text excerpt" in content[0]["text"]

def test_visual_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of VisualStrategy."""
    strategy = VisualStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]

def test_table_chunk_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of TableChunkStrategy."""
    strategy = TableChunkStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]

def test_table_focused_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of TableFocusedStrategy."""
    strategy = TableFocusedStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]

def test_text_only_strategy_create_content(mock_page_data, mock_plan, mock_config):
    """Tests the _create_content method of TextOnlyStrategy."""
    strategy = TextOnlyStrategy(client=MagicMock())
    content = strategy._create_content(mock_page_data, mock_plan, mock_config)
    assert isinstance(content[0]["text"], str) and len(content[0]["text"]) > 0
    assert "Test instructions" in content[0]["text"]
