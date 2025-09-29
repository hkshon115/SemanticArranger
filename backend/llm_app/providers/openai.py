"""
This module provides the specific implementation for interacting with the
OpenAI API. It adapts the standard chat format to the format expected
by the OpenAI API.
"""
import asyncio
from typing import Optional
from .base import BaseProvider
from ..utils.retry import RetryConfig

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def _convert_to_openai_content(self, content: list) -> list:
    openai_content = []
    for item in content:
        if item.get("type") == "text":
            openai_content.append(item)
        elif item.get("type") == "image":
            source = item.get("source", {})
            if source.get("type") == "base64":
                media_type = source.get("media_type")
                b64_data = source.get("data")
                prefix = "data:"
                data_url = prefix + media_type + ";base64," + b64_data
                openai_content.append({
                    "type": "image_url",
                    "image_url": {"url": data_url}
                })
    return openai_content

class _OpenAI(BaseProvider):
    def __init__(self, api_key: str, retry_config: Optional[RetryConfig] = None):
        super().__init__(api_key, retry_config)
        self.sync_client = OpenAI(api_key=api_key)

    def _get_messages(self, content: list, system: str) -> list:
        openai_formatted_content = _convert_to_openai_content(content)
        return [{"role": "system", "content": system}, {"role": "user", "content": openai_formatted_content}]

    def send_message(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        messages = self._get_messages(content, system)
        
        params = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'timeout': timeout
        }
        
        for key in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 'seed', 'response_format', 'tools', 'tool_choice']:
            if key in kwargs:
                params[key] = kwargs[key]
        
        completion = self._execute_with_retry(
            self.sync_client.chat.completions.create,
            **params
        )
        return completion.model_dump()

    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        messages = self._get_messages(content, system)
        
        params = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'timeout': timeout,
            'stream': True
        }
        
        for key in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 'seed']:
            if key in kwargs:
                params[key] = kwargs[key]
        
        return self._execute_with_retry(
            self.sync_client.chat.completions.create,
            **params
        )

class _AsyncOpenAI(BaseProvider):
    def __init__(self, api_key: str, retry_config: Optional[RetryConfig] = None):
        super().__init__(api_key, retry_config)
        self.async_client = AsyncOpenAI(api_key=api_key)

    def _get_messages(self, content: list, system: str) -> list:
        openai_formatted_content = _convert_to_openai_content(content)
        return [{"role": "system", "content": system}, {"role": "user", "content": openai_formatted_content}]

    async def send_message_async(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        messages = self._get_messages(content, system)
        
        params = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'timeout': timeout
        }
        
        for key in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 'seed', 'response_format', 'tools', 'tool_choice']:
            if key in kwargs:
                params[key] = kwargs[key]
        
        completion = await self._execute_with_retry_async(
            self.async_client.chat.completions.create,
            **params
        )
        return completion.model_dump()

    async def send_message_stream_async(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        messages = self._get_messages(content, system)
        
        params = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'timeout': timeout,
            'stream': True
        }
        
        for key in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'stop', 'seed']:
            if key in kwargs:
                params[key] = kwargs[key]
        
        return self._execute_with_retry_async(
            self.async_client.chat.completions.create,
            **params
        )

    def send_message(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        """Synchronous wrapper for async send_message_async"""
        return asyncio.run(self.send_message_async(model, content, system, max_tokens, timeout, **kwargs))

    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        """Returns an async generator for streaming - must be used in async context"""
        async def async_generator():
            async for item in self.send_message_stream_async(model, content, system, max_tokens, timeout, **kwargs):
                yield item
        return async_generator()

    async def close(self):
        await self.async_client.close()