"""
Unit tests for the extraction strategy factory.
"""
import pytest
from unittest.mock import MagicMock
from backend.strategies.factory import register_strategy, get_strategy
from backend.strategies.base import IExtractionStrategy

# Create a mock strategy for testing
class MockStrategy(IExtractionStrategy):
    def __init__(self, client):
        self.client = client

    async def execute_plan(self, plan, page_data, config):
        pass

def test_register_and_get_strategy():
    """Tests that a strategy can be registered and then retrieved."""
    mock_client = MagicMock()
    register_strategy("mock_strategy", MockStrategy)
    
    strategy = get_strategy("mock_strategy", client=mock_client)
    
    assert isinstance(strategy, MockStrategy)
    assert strategy.client == mock_client

def test_get_unregistered_strategy_raises_error():
    """Tests that requesting an unregistered strategy raises a ValueError."""
    with pytest.raises(ValueError):
        get_strategy("unregistered_strategy")
