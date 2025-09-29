import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.resilience.token_limit_handler import TokenLimitHandler

@pytest.mark.asyncio
async def test_execute_with_token_retry_success_on_first_try():
    """
    Tests that the operation succeeds on the first try without any retry.
    """
    handler = TokenLimitHandler()
    mock_operation = AsyncMock(return_value="Success")
    
    result = await handler.execute_with_token_retry(
        mock_operation, max_tokens=1000
    )
    
    assert result == "Success"
    mock_operation.assert_called_once_with(max_tokens=1000)

@pytest.mark.asyncio
async def test_execute_with_token_retry_on_token_limit_error():
    """
    Tests that a retry is triggered on a token limit error with a boosted token count.
    """
    handler = TokenLimitHandler(token_boost_value=5000)
    
    # Simulate a token limit error on the first call, success on the second
    mock_operation = AsyncMock(side_effect=[
        Exception("The response was truncated due to max_tokens."),
        "Success on retry"
    ])
    
    result = await handler.execute_with_token_retry(
        mock_operation, max_tokens=1000, other_arg="test"
    )
    
    assert result == "Success on retry"
    assert mock_operation.call_count == 2
    
    # Check args of the first call
    first_call_args = mock_operation.call_args_list[0]
    assert first_call_args[1]['max_tokens'] == 1000
    
    # Check args of the second (retry) call
    second_call_args = mock_operation.call_args_list[1]
    assert second_call_args[1]['max_tokens'] == 5000
    assert second_call_args[1]['other_arg'] == "test"

@pytest.mark.asyncio
async def test_execute_with_token_retry_fails_on_other_error():
    """
    Tests that no retry is attempted for a non-token-limit error.
    """
    handler = TokenLimitHandler()
    mock_operation = AsyncMock(side_effect=ValueError("A different error"))
    
    with pytest.raises(ValueError, match="A different error"):
        await handler.execute_with_token_retry(
            mock_operation, max_tokens=1000
        )
        
    mock_operation.assert_called_once()
