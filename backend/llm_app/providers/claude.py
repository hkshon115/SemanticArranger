"""
This module provides the specific implementation for interacting with the
Claude API. It adapts the standard chat format to the format expected
by the Claude API using the `anthropic` SDK.
"""
import asyncio
from typing import Optional
from .base import BaseProvider
import json
import anthropic

try:
    import aiohttp
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

def _convert_to_claude_parts(content: list) -> list:
    claude_parts =[]
    for item in content:
        if item.get("type")== "text":
            claude_parts.append({"type": "text", "text": item.get("text","")})
        elif item.get("type")=="image" and "source" in item:
            source = item["source"]
            if source.get("type")=="base64":
                claude_parts.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": source.get("media_type"),
                        "data": source.get("data")
                    }
                })
    return claude_parts

class _ClaudeAPI(BaseProvider):
    def __init__(self, api_key: str, retry_config=None):
        super().__init__(api_key, retry_config)
        self.sync_client = anthropic.Anthropic(api_key=api_key)

    def send_message(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        claude_content = _convert_to_claude_parts(content)
        
        response = self._execute_with_retry(
            self.sync_client.messages.create,
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{'role': 'user', 'content': claude_content}],
            timeout=timeout,
            **kwargs
        )
        
        return {"content": response.content[0].text, "usage": {}}

    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        claude_content = _convert_to_claude_parts(content)
        
        stream = self._execute_with_retry(
            self.sync_client.messages.stream,
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{'role': 'user', 'content': claude_content}],
            timeout=timeout,
            **kwargs
        )
        
        for chunk in stream:
            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                yield {"content": chunk.delta.text}

class _AsyncClaudeAPI(BaseProvider):
    def __init__(self, api_key: str, retry_config=None):
        super().__init__(api_key, retry_config)
        import httpx
        self.async_client = anthropic.AsyncAnthropic(
            api_key=api_key,
            http_client=httpx.AsyncClient(
                verify=False
            )
        )

    async def send_message_async(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        claude_content = _convert_to_claude_parts(content)
        print(f"--Using Claude model: {model}--")
        response = await self._execute_with_retry_async(
            self.async_client.messages.create,
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{'role': 'user', 'content': claude_content}],
            timeout=timeout,
            **kwargs
        )
        
        return {"content": response.content[0].text, "usage": {}}

    async def send_message_stream_async(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        claude_content = _convert_to_claude_parts(content)
        
        stream = await self._execute_with_retry_async(
            self.async_client.messages.stream,
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{'role': 'user', 'content': claude_content}],
            timeout=timeout,
            **kwargs
        )
        
        async for chunk in stream:
            if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                yield {"content": chunk.delta.text}

    def send_message(self, model : str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        import asyncio
        return asyncio.run(self.send_message_async(model, content, system, max_tokens, timeout, **kwargs))
    
    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        async def async_generator():
            async for item in self.send_message_stream_async(model, content, system, max_tokens, timeout, **kwargs):
                yield item
        return async_generator()