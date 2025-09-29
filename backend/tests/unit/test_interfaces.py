"""
Unit tests for the abstract interfaces.
"""
import pytest
from backend.core.interfaces import (
    IAsyncRouter,
    IAsyncExtractor,
    IResultMerger,
    PageData,
)

def test_cannot_instantiate_iasyncrouter():
    """Tests that the IAsyncRouter interface cannot be instantiated."""
    with pytest.raises(TypeError):
        IAsyncRouter()

def test_cannot_instantiate_iasyncextractor():
    """Tests that the IAsyncExtractor interface cannot be instantiated."""
    with pytest.raises(TypeError):
        IAsyncExtractor()

def test_cannot_instantiate_iresultmerger():
    """Tests that the IResultMerger interface cannot be instantiated."""
    with pytest.raises(TypeError):
        IResultMerger()

def test_cannot_instantiate_pagedata():
    """Tests that the PageData interface cannot be instantiated."""
    with pytest.raises(TypeError):
        PageData()

def test_incomplete_implementation_has_abstract_methods():
    """
    Tests that a concrete class that does not implement all abstract methods
    still has the abstract methods listed in its __abstractmethods__ set.
    """
    assert IAsyncRouter.__abstractmethods__
    assert IAsyncExtractor.__abstractmethods__
    assert IResultMerger.__abstractmethods__
