"""
This module provides a provider for interacting with a local LLM server
that is compatible with the OpenAI API format.
"""
from .base import BaseProvider
from ..utils.session import get_shared_session
import json

class _LocalLLMAPI(BaseProvider):
    def __init__(self, api_key: str = "not_needed", retry_config=None, base_url: str = 'http://localhost:8080/v1/chat/completions'):
        super().__init__(api_key, retry_config)
        self.base_url = base_url
        self.session = get_shared_session()
        self.headers = {'Content-Type': 'application/json'}

    def _make_request(self, data: dict, timeout: int, stream: bool = False):
        if stream:
            return self.session.post(self.base_url, json=data, headers=self.headers, timeout=timeout, stream=True)
        else:
            response = self.session.post(self.base_url, json=data, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response.json()

    def send_message(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        data = {
            'model': model, 
            'max_tokens': max_tokens, 
            'stream': False, 
            'messages': [
                {"role": "system", "content": system},
                {'role': 'user', 'content': content}
            ]
        }
        
        for key in ['temperature', 'top_p', 'top_k', 'stop']:
            if key in kwargs:
                data[key] = kwargs[key]
        
        return self._execute_with_retry(self._make_request, data, timeout)

    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        data = {
            'model': model, 
            'max_tokens': max_tokens, 
            'stream': True, 
            'messages': [
                {"role": "system", "content": system},
                {'role': 'user', 'content': content}
            ]
        }
        
        for key in ['temperature', 'top_p', 'top_k', 'stop']:
            if key in kwargs:
                data[key] = kwargs[key]
            
        response = self._execute_with_retry(self._make_request, data, timeout, stream=True)
        
        with response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        json_str = line_str[6:].strip()
                        if json_str != '[DONE]':
                            yield json.loads(json_str)
