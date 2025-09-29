import pytest
from unittest.mock import AsyncMock, MagicMock

# Import the factory functions and the internal map for testing purposes
from backend.strategies.factory import get_strategy, register_strategy, _strategy_map
from backend.strategies.base import IExtractionStrategy, BaseStrategy
from backend.models.extraction import ExtractionPlan, ExtractionResult, ExtractionStrategy
from backend.core.interfaces import PageData
from backend.config.pipeline_config import PipelineConfig

# Import a concrete strategy to ensure it's registered for testing
from backend.strategies.minimal import MinimalStrategy

# Mock AsyncLLMClient for dependency injection
mock_client = AsyncMock()

# A dummy strategy for testing registration in isolation
class MockStrategy(IExtractionStrategy):
    def __init__(self, client: AsyncMock):
        self.client = client

    async def execute_plan(
        self, plan: ExtractionPlan, page_data: PageData, config: any
    ) -> ExtractionResult:
        return ExtractionResult(
            step=1, strategy="mock", success=True, content={"mock": "result"}
        )

@pytest.fixture(autouse=True)
def clear_strategy_map():
    """
    Fixture to clear the strategy map before each test to ensure isolation.
    It runs automatically for every test in this file.
    """
    _strategy_map.clear()
    # Re-register the minimal strategy for the placeholder test
    register_strategy("minimal", MinimalStrategy)
    yield
    _strategy_map.clear()

def test_register_strategy():
    """
    Validates that a new strategy can be registered in the factory's map.
    """
    assert "mock" not in _strategy_map
    register_strategy("mock", MockStrategy)
    assert "mock" in _strategy_map
    assert _strategy_map["mock"] == MockStrategy

def test_get_strategy_success():
    """
    Validates that a registered strategy can be retrieved successfully from the factory.
    """
    register_strategy("mock", MockStrategy)
    strategy_instance = get_strategy("mock", client=mock_client)
    assert isinstance(strategy_instance, MockStrategy)
    assert strategy_instance.client == mock_client

def test_get_strategy_not_found():
    """
    Validates that attempting to retrieve an unregistered strategy raises a ValueError.
    """
    with pytest.raises(ValueError, match="Unknown strategy: non_existent_strategy"):
        get_strategy("non_existent_strategy")

@pytest.mark.asyncio
async def test_placeholder_strategy_execution_success():
    """
    Tests the successful execution of a placeholder strategy.
    """
    # Prepare mock inputs
    mock_plan = ExtractionPlan(
        step=1,
        description="Test plan for minimal strategy",
        strategy=ExtractionStrategy.MINIMAL,
        max_tokens=1000,
    )
    mock_page_data = MagicMock(spec=PageData)
    mock_page_data.get_image.return_value = b"test_image_bytes"
    mock_page_data.get_text.return_value = "test page text"
    mock_config = MagicMock()
    mock_config.key_lang = "en"
    mock_config.extraction_primary_model = "test-model"

    # Configure the mock client to return a successful response
    mock_client.chat.return_value = {
        "content": '{"status": "executed"}',
        "usage": {"total_tokens": 50},
    }

    strategy = get_strategy("minimal", client=mock_client)
    result = await strategy.execute_plan(mock_plan, mock_page_data, mock_config)

    assert result.success is True
    assert result.content == {"status": "executed"}
    assert result.tokens_used == 50

@pytest.mark.asyncio
async def test_placeholder_strategy_execution_failure():
    """
    Tests the failure path of a placeholder strategy.
    """
    # Prepare mock inputs
    mock_plan = ExtractionPlan(
        step=1,
        description="Test plan for minimal strategy",
        strategy=ExtractionStrategy.MINIMAL,
        max_tokens=1000,
    )
    mock_page_data = MagicMock(spec=PageData)
    mock_page_data.get_image.return_value = b"test_image_bytes"
    mock_page_data.get_text.return_value = "test page text"
    mock_config = MagicMock()
    mock_config.key_lang = "en"
    mock_config.extraction_primary_model = "test-model"

    # Configure the mock client to return an error response
    mock_client.chat.return_value = {"error": "LLM failed"}

    strategy = get_strategy("minimal", client=mock_client)
    result = await strategy.execute_plan(mock_plan, mock_page_data, mock_config)

    assert result.success is False
    assert result.error == "LLM failed"

# A concrete implementation of BaseStrategy for testing purposes
class MockConcreteStrategy(BaseStrategy):
    def _create_content(self, page_data, plan, config):
        # Return a mock content structure
        return [{"type": "text", "text": "Mock prompt"}]

@pytest.mark.asyncio
async def test_base_strategy_execute_plan_success():
    """
    Tests the successful execution of the execute_plan method in BaseStrategy.
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.chat.return_value = {
        "content": '{"key": "value"}',
        "usage": {"total_tokens": 100},
    }
    
    strategy = MockConcreteStrategy(client=mock_client)
    plan = ExtractionPlan(step=1, description="Test", strategy=ExtractionStrategy.MINIMAL, max_tokens=1000)
    page_data = MagicMock()
    config = PipelineConfig(extraction_primary_model="test-model")

    # Act
    result = await strategy.execute_plan(plan, page_data, config)

    # Assert
    assert result.success is True
    assert result.content == {"key": "value"}
    assert result.tokens_used == 100
    assert result.error is None
    mock_client.chat.assert_called_once()

@pytest.mark.asyncio
async def test_base_strategy_execute_plan_api_error():
    """
    Tests that execute_plan correctly handles an error from the LLM API.
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.chat.return_value = {"error": "API limit reached"}
    
    strategy = MockConcreteStrategy(client=mock_client)
    plan = ExtractionPlan(step=1, description="Test", strategy=ExtractionStrategy.MINIMAL, max_tokens=1000)
    page_data = MagicMock()
    config = PipelineConfig()

    # Act
    result = await strategy.execute_plan(plan, page_data, config)

    # Assert
    assert result.success is False
    assert result.error == "API limit reached"
    assert result.content is None

@pytest.mark.asyncio
async def test_base_strategy_execute_plan_json_parse_error():
    """
    Tests that execute_plan handles a malformed JSON response from the LLM.
    """
    # Arrange
    mock_client = AsyncMock()
    mock_client.chat.return_value = {
        "content": "This is not JSON",
        "usage": {"total_tokens": 50},
    }
    
    strategy = MockConcreteStrategy(client=mock_client)
    plan = ExtractionPlan(step=1, description="Test", strategy=ExtractionStrategy.MINIMAL, max_tokens=1000)
    page_data = MagicMock()
    config = PipelineConfig()

    # Act
    result = await strategy.execute_plan(plan, page_data, config)

    # Assert
    assert result.success is False
    assert result.error == "Failed to parse JSON response from the model."
    assert result.tokens_used == 50