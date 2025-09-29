"""
Unit tests for the structured logger utility.
"""
import json
import logging
from io import StringIO
import pytest
from backend.utils.logger import configure_logging, get_logger, get_correlation_id, correlation_id_var

@pytest.fixture(autouse=True)
def reset_logging():
    """Fixture to reset logging configuration before each test."""
    import structlog
    structlog.reset_defaults()

def test_logger_produces_json_output():
    """Tests that the logger outputs structured JSON."""
    log_stream = StringIO()
    
    # Get the root logger and add a handler that writes to our stream
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(log_stream)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    configure_logging()
    
    logger = get_logger("test_json_output")
    logger.info("test_event", key="value")
    
    # Remove the handler to avoid side effects
    root_logger.removeHandler(handler)
    
    log_output = log_stream.getvalue()
    log_data = json.loads(log_output)
    
    assert log_data["event"] == "test_event"
    assert log_data["key"] == "value"
    assert "correlation_id" in log_data

def test_correlation_id_generation():
    """Tests that a correlation ID is generated if none exists."""
    correlation_id = get_correlation_id()
    assert isinstance(correlation_id, str)
    assert len(correlation_id) > 0

def test_correlation_id_is_consistent_within_context():
    """Tests that the correlation ID is consistent within the same context."""
    correlation_id_var.set("test-id")
    
    log_stream = StringIO()
    root_logger = logging.getLogger()
    handler = logging.StreamHandler(log_stream)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    configure_logging()
    
    logger = get_logger("test_consistency")
    logger.info("first_event")
    logger.warning("second_event")
    
    root_logger.removeHandler(handler)
    
    log_outputs = log_stream.getvalue().strip().split('\n')
    log_data1 = json.loads(log_outputs[0])
    log_data2 = json.loads(log_outputs[1])
    
    assert log_data1["correlation_id"] == "test-id"
    assert log_data2["correlation_id"] == "test-id"

def test_different_correlation_ids_for_different_contexts():
    """Tests that different contexts get different correlation IDs."""
    # This is a simplified simulation of different async contexts
    
    # Context 1
    correlation_id_var.set("context-1")
    id1 = get_correlation_id()
    
    # Context 2
    correlation_id_var.set("context-2")
    id2 = get_correlation_id()
    
    assert id1 == "context-1"
    assert id2 == "context-2"
    assert id1 != id2
