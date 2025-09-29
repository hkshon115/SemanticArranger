import pytest
from backend.utils.token_estimator import TokenEstimator, estimate_tokens

@pytest.fixture(autouse=True)
def clear_cache():
    """Fixture to clear the lru_cache before each test."""
    from backend.utils.token_estimator import default_estimator
    default_estimator.estimate_tokens.cache_clear()

def test_token_estimator_gpt4():
    """
    Tests the token estimator with the gpt-4 tokenizer.
    """
    estimator = TokenEstimator(model_name="gpt-4")
    assert estimator.estimate_tokens("Hello world") == 2
    assert estimator.estimate_tokens("This is a test.") == 5

def test_token_estimator_fallback():
    """
    Tests that the token estimator falls back to a default tokenizer for unknown models.
    """
    estimator = TokenEstimator(model_name="unknown-model")
    # The fallback tokenizer should still produce a reasonable estimate
    assert estimator.estimate_tokens("Hello world") > 0

def test_token_estimator_caching():
    """
    Tests that the token estimator caches results for repeated calls.
    """
    estimator = TokenEstimator()
    text = "This is a long string that will be cached."
    
    # The first call will populate the cache
    estimator.estimate_tokens(text)
    
    # The second call should be a cache hit
    estimator.estimate_tokens(text)
    
    # Check the cache info
    assert estimator.estimate_tokens.cache_info().hits == 1

def test_convenience_function():
    """
    Tests the global estimate_tokens convenience function.
    """
    assert estimate_tokens("Hello world") == 2

def test_handle_non_string_input():
    """
    Tests that the estimator handles non-string input gracefully.
    """
    assert estimate_tokens(None) == 0
    assert estimate_tokens(123) == 0
