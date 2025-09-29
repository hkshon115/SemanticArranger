"""
Core Extractor Module for the Extraction Pipeline.

This module contains the AsyncExtractor, which is responsible for executing
a step-by-step extraction plan for a single document page.
"""
import asyncio
import base64
import json
import re
import time
from typing import List, Dict, Any, Optional

from backend.config.llm_config import LLMConfig
from backend.config.prompt_templates import get_extraction_prompt
from backend.core.interfaces import IAsyncExtractor, PageData
from backend.llm_app.async_client import AsyncLLMClient
from backend.models.extraction import (
    ExtractionPlan,
    ExtractionResult,
)
from backend.resilience.token_limit_handler import TokenLimitHandler

class AsyncExtractor(IAsyncExtractor):
    """
    Executes a step-by-step extraction plan for a single document page.

    This class is responsible for taking a specific `ExtractionPlan` from the
    `AsyncRouter`, preparing the content and prompt, and calling the LLM to
    extract the requested information. It also handles response parsing and
    error management for a single extraction step.
    """

    def __init__(self, client: AsyncLLMClient, llm_config: LLMConfig):
        """
        Initializes the AsyncExtractor.

        Args:
            client: An instance of `AsyncLLMClient` for making API calls.
            llm_config: The LLM configuration object.
        """
        self.client = client
        self.llm_config = llm_config
        self.token_handler = TokenLimitHandler()

    async def execute_plan(
        self, plan: ExtractionPlan, page_data: PageData, key_lang: str = "en"
    ) -> ExtractionResult:
        """
        Executes a single step of an extraction plan.

        This method prepares the prompt and content, calls the LLM, and wraps
        the outcome in an `ExtractionResult` object, handling any potential
        errors during the process.

        Args:
            plan: The `ExtractionPlan` for the current step.
            page_data: The `PageData` object containing the page's text and image.
            key_lang: The target language for the extraction.

        Returns:
            An `ExtractionResult` object with the outcome of the extraction.
        """
        start_time = time.time()
        
        model_name = self.llm_config.extraction_primary_model
        
        prompt = get_extraction_prompt(
            strategy=plan.strategy,
            special_instructions=plan.special_instructions,
            key_lang=key_lang,
        )
        
        content = self._prepare_extractor_content(prompt, page_data)
        
        try:
            response = await self.token_handler.execute_with_token_retry(
                self.client.chat,
                model=model_name,
                content=content,
                system="You are a precise document analyzer. Return only valid JSON.",
                max_tokens=plan.max_tokens,
                temperature=0.1,
                timeout=120 if plan.estimated_complexity == "high" else 90,
            )
            
            elapsed = time.time() - start_time
            
            if response.get("error"):
                return self._create_error_result(plan, response["error"], elapsed)

            if response.get("content"):
                parsed_content = self._parse_extraction_response(response["content"])
                if parsed_content:
                    return ExtractionResult(
                        step=plan.step,
                        strategy=plan.strategy.value,
                        success=True,
                        content=parsed_content,
                        tokens_used=response.get("usage", {}).get("total_tokens", 0),
                        time_elapsed=elapsed,
                        model_used=model_name,
                    )
            
            return self._create_error_result(plan, "Failed to parse JSON from model response.", elapsed)

        except Exception as e:
            elapsed = time.time() - start_time
            return self._create_error_result(plan, str(e), elapsed)

    def _prepare_extractor_content(self, prompt: str, page_data: PageData) -> List[Dict[str, Any]]:
        """Prepares the content payload for the extractor LLM."""
        content = [{"type": "text", "text": prompt}]
        try:
            base64_data = base64.b64encode(page_data.get_image()).decode("utf-8")
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64_data,
                },
            })
        except Exception as e:
            print(f"Image encoding error: {e}. Proceeding with text-only extraction.")
        return content

    def _parse_extraction_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parses the JSON response from the extractor LLM."""
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                cleaned_content = json_match.group(0)
                return json.loads(cleaned_content)
        except (json.JSONDecodeError, TypeError):
            return None
        return None

    def _create_error_result(self, plan: ExtractionPlan, error: str, time_elapsed: float) -> ExtractionResult:
        """Creates an ExtractionResult for a failed extraction."""
        return ExtractionResult(
            step=plan.step,
            strategy=plan.strategy.value,
            success=False,
            error=error,
            time_elapsed=time_elapsed,
        )
