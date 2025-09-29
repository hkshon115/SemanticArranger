"""
This module provides the specific implementation for interacting with the
Google Gemini API. It adapts the standard chat format to the format expected
by the Gemini API using the `google-generativeai` SDK.
"""
from .base import BaseProvider
from ..utils.session import get_shared_session, get_shared_async_session
import json
import requests
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

try:
    import aiohttp
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def _convert_to_gemini_parts(content: list) -> list:
    gemini_parts =[]
    for item in content:
        if item.get("type")== "text":
            gemini_parts.append({"text": item.get("text","")})
        elif item.get("type")=="image":
            source = item.get("source",{})
            if source.get("type")=="base64":
                gemini_parts.append({
                    "inline_data": {
                        "mime_type": source.get("media_type"),
                        "data": source.get("data")
                    }
                })
    return gemini_parts

class _GeminiAPI(BaseProvider):
    def __init__(self, api_key: str, retry_config=None):
        super().__init__(api_key, retry_config)
        genai.configure(api_key=api_key)

    def send_message(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        gemini_parts = _convert_to_gemini_parts(content)
        generation_config = GenerationConfig(max_output_tokens=max_tokens)
        
        gemini_model = genai.GenerativeModel(model, system_instruction=system)
        
        response = self._execute_with_retry(
            gemini_model.generate_content,
            gemini_parts,
            generation_config=generation_config,
            request_options={'timeout': timeout}
        )
        
        return {"content": response.text, "usage": {}}

    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        gemini_parts = _convert_to_gemini_parts(content)
        generation_config = GenerationConfig(max_output_tokens=max_tokens)
        
        gemini_model = genai.GenerativeModel(model, system_instruction=system)
        
        stream = self._execute_with_retry(
            gemini_model.generate_content,
            gemini_parts,
            generation_config=generation_config,
            stream=True,
            request_options={'timeout': timeout}
        )
        
        for chunk in stream:
            yield {"content": chunk.text}

class _AsyncGeminiAPI(BaseProvider):
    def __init__(self, api_key: str, retry_config=None):
        super().__init__(api_key, retry_config)
        genai.configure(api_key=api_key)

    async def send_message_async(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        gemini_parts = _convert_to_gemini_parts(content)
        generation_config = GenerationConfig(max_output_tokens=max_tokens)
        
        gemini_model = genai.GenerativeModel(model, system_instruction=system)
        
        response = await self._execute_with_retry_async(
            gemini_model.generate_content_async,
            gemini_parts,
            generation_config=generation_config,
            request_options={'timeout': timeout}
        )
        
        return {"content": response.text, "usage": {}}

    async def send_message_stream_async(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        gemini_parts = _convert_to_gemini_parts(content)
        generation_config = GenerationConfig(max_output_tokens=max_tokens)
        
        gemini_model = genai.GenerativeModel(model, system_instruction=system)
        
        stream = await self._execute_with_retry_async(
            gemini_model.generate_content_async,
            gemini_parts,
            generation_config=generation_config,
            stream=True,
            request_options={'timeout': timeout}
        )
        
        async for chunk in stream:
            yield {"content": chunk.text}
    def send_message(self, model : str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        import asyncio
        return asyncio.run(self.send_message_async(model, content, system, max_tokens,
        timeout, **kwargs))
        
    def send_message_stream(self, model: str, content: list, system: str, max_tokens: int, timeout: int, **kwargs):
        async def async_generator():
            async for item in self.send_message_stream_async(model, content, system, max_tokens, timeout, **kwargs):
                yield item
        return async_generator()