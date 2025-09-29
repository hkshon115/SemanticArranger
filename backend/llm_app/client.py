import os
from typing import Dict, Optional, Any, Iterator, List, Union
from collections import defaultdict
from .providers.claude import _ClaudeAPI
from .providers.gemini import _GeminiAPI
from .providers.openai import _OpenAI, OPENAI_AVAILABLE
from .utils.retry import RetryConfig
from .error_handler import LLMErrorAnalyzer, ERROR_HANDLER_AVAILABLE

from .providers.local_llm import _LocalLLMAPI


class LLMClient:
    """
    A synchronous client for interacting with multiple LLM providers.

    This client provides a blocking interface for making API calls to different
    LLM providers. It is a synchronous wrapper around the provider-specific
    implementations.
    """
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initializes the synchronous LLM client.

        Args:
            retry_config: Configuration for retry behavior on failed API calls.
        """
        self.retry_config = retry_config or RetryConfig()
        self._token_usage = defaultdict(lambda: defaultdict(int))
        self._clients = {}

        # Conditionally initialize providers if their API keys are available
        if os.environ.get('CLAUDE_API_KEY'):
            self._clients['claude'] = _ClaudeAPI(os.environ.get('CLAUDE_API_KEY'), self.retry_config)
        if os.environ.get('GEMINI_API_KEY'):
            self._clients['gemini'] = _GeminiAPI(os.environ.get('GEMINI_API_KEY'), self.retry_config)
        if OPENAI_AVAILABLE and os.environ.get('OPENAI_API_KEY'):
            self._clients['openai'] = _OpenAI(os.environ.get('OPENAI_API_KEY'), self.retry_config)
        if os.environ.get('LOCAL_LLM_ENDPOINT'):
            self._clients['local'] = _LocalLLMAPI(None, self.retry_config, base_url=os.environ.get('LOCAL_LLM_ENDPOINT'))

        if not self._clients:
            print("⚠️ No LLM API keys or local endpoint found. Please set at least one of the following environment variables: CLAUDE_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, LOCAL_LLM_ENDPOINT")

    def _get_client_for_model(self, model_name: str) -> Optional[Any]:
        """
        Selects the appropriate provider client based on the model name.
        """
        if 'claude' in model_name: return self._clients.get('claude')
        if 'gemini' in model_name: return self._clients.get('gemini')
        if 'gpt' in model_name: return self._clients.get('openai')
        if 'local' in model_name: return self._clients.get('local')
        return None

    def _normalize_content(self, content: Union[str, List[Dict]]) -> List[Dict]:
        """
        Ensures that the content is in the standardized list-of-dicts format.
        """
        if isinstance(content, str):
            return [{"type": "text", "text": content}]
        return content

    def _update_token_tracker(self, model: str, usage: Dict[str, int]):
        """
        Updates the token usage statistics for a given model.
        """
        self._token_usage[model]['prompt_tokens'] += usage.get('prompt_tokens', 0)
        self._token_usage[model]['completion_tokens'] += usage.get('completion_tokens', 0)
        self._token_usage[model]['total_tokens'] += usage.get('total_tokens', 0)
        self._token_usage[model]['requests'] += 1
        
    def get_usage_summary(self) -> Dict:
        """
        Returns a summary of token usage across all models.
        """
        summary = {
            "models": dict(self._token_usage),
            "grand_total": {
                "prompt_tokens": sum(data['prompt_tokens'] for data in self._token_usage.values()),
                "completion_tokens": sum(data['completion_tokens'] for data in self._token_usage.values()),
                "total_tokens": sum(data['total_tokens'] for data in self._token_usage.values()),
                "total_requests": sum(data['requests'] for data in self._token_usage.values())
            }
        }
        return summary

    def _parse_response(self, model: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses the raw response from a provider into a standardized format.
        """
        if not response:
            return {'content': None, 'usage': {}}
            
        model_lower = model.lower()
        
        if 'gemini' in model_lower:
            if response.get('candidates'):
                response['content'] = response['candidates'][0]['content']['parts'][0]['text']
                response['usage'] = response.get('usageMetadata', {})
        elif 'claude' in model_lower:
            # The content is already extracted in the provider
            pass
        elif 'gpt' in model_lower:
            if response.get('choices'):
                response['content'] = response['choices'][0]['message']['content']
        
        return response

    def chat(self, model: str, content: Union[str, List[Dict]], system: str = "You are a helpful assistant.", 
             max_tokens: int = 2048, timeout: int = 120, **kwargs) -> Dict[str, Any]:
        """
        Sends a chat message to the specified model and gets a response.

        Args:
            model: The name of the model to use.
            content: The message content.
            system: The system prompt.
            max_tokens: The maximum number of tokens to generate.
            timeout: The timeout for the API call.
            **kwargs: Additional parameters for the provider.

        Returns:
            A dictionary containing the response content and usage statistics.
        """
        client = self._get_client_for_model(model)
        if not client:
            return {'content': None, 'error': f"No client for model '{model}'.", 'usage': {}}
        
        normalized_content = self._normalize_content(content)
        
        response = client.send_message(
            model=model, content=normalized_content, system=system, 
            max_tokens=max_tokens, timeout=timeout, **kwargs
        )
        
        parsed_response = self._parse_response(model, response)
        
        if parsed_response and 'usage' in parsed_response:
            self._update_token_tracker(model, parsed_response['usage'])
            
        return parsed_response
    def chat_stream(self, model: str, content: Union[str, List[Dict]], system: str = "You are a helpful assistant.", 
                    max_tokens: int = 2048, timeout: int = 120, **kwargs) -> Iterator[str]:
        """
        Sends a chat message and streams the response.

        Args:
            model: The name of the model to use.
            content: The message content.
            system: The system prompt.
            max_tokens: The maximum number of tokens to generate.
            timeout: The timeout for the API call.
            **kwargs: Additional parameters for the provider.

        Yields:
            Chunks of the response as they are received.
        """
