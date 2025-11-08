"""
Core Router Module for the Extraction Pipeline.

This module contains the AsyncRouter, which is responsible for analyzing a
document page and creating a detailed, step-by-step extraction plan.
"""
import asyncio
import base64
import json
import re
from typing import List, Dict, Any

from backend.config.llm_config import LLMConfig
from backend.config.prompt_templates import ROUTER_ANALYSIS_PROMPT
from backend.core.interfaces import IAsyncRouter, PageData
from backend.llm_app.async_client import AsyncLLMClient
from backend.models.extraction import (
    ExtractionPlan,
    ExtractionStrategy,
    RouterAnalysis,
)
from backend.utils.validators import detect_legal_financial_content


class AsyncRouter(IAsyncRouter):
    """
    Analyzes a document page using a vision-capable LLM to create a strategic,
    step-by-step extraction plan. It implements model fallback chains for
    resilience against API failures.
    """

    def __init__(self, client: AsyncLLMClient, llm_config: LLMConfig):
        """
        Initializes the AsyncRouter.

        Args:
            client: An instance of `AsyncLLMClient` for making API calls.
            llm_config: The LLM configuration object.
        """
        self.client = client
        self.llm_config = llm_config

    async def analyze_page(self, page_data: PageData, key_lang: str = "en") -> RouterAnalysis:
        """
        Analyzes a single page and returns a structured extraction plan.

        This method sends the page image and text to an LLM and asks it to
        assess the page's complexity, identify content types, and create a
        plan. It will automatically try fallback models if the primary
        model fails.

        Args:
            page_data: The `PageData` object containing the page's text and image.
            key_lang: The target language for the analysis.

        Returns:
            A `RouterAnalysis` object containing the generated extraction plan.
        """
        # Prepare content for the router LLM
        content = self._prepare_router_content(page_data, key_lang)

        # Use the configured model chain for analysis
        model_chain = self._get_fallback_chain(self.llm_config.router_model)
        
        for attempt, model_name in enumerate(model_chain):
            if attempt > 0:
                await asyncio.sleep(1.0)  # Pause before retry

            try:
                response = await self.client.chat(
                    model=model_name,
                    content=content,
                    system="You are an expert document analyzer. Provide detailed extraction plans. Return ONLY valid JSON.",
                    max_tokens=3000,
                    temperature=0.1,
                    timeout=120,
                )

                if response.get("content"):
                    return self._parse_router_response(response["content"])
                
            except Exception as e:
                # Log the error and try the next model in the chain
                print(f"Router exception with {model_name}: {e}")
                continue
        
        # If all models in the chain fail, create a fallback plan
        return self._create_fallback_plan()

    def _prepare_router_content(self, page_data: PageData, key_lang: str) -> List[Dict[str, Any]]:
        """Prepares the content payload for the router LLM."""
        router_prompt = f"IMPORTANT: Write all your analysis, descriptions, and insights in {key_lang} language.\n{ROUTER_ANALYSIS_PROMPT}"
        
        content = [{"type": "text", "text": router_prompt}]
        
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
            print(f"Image encoding error: {e}. Proceeding with text-only analysis.")

        page_text = page_data.get_text()
        if page_text:
            text_preview = page_text[:500] + "..." if len(page_text) > 500 else page_text
            content[0]["text"] += f"\n\nText preview from page:\n{text_preview}"
            
        return content

    def _get_fallback_chain(self, primary_model: str) -> List[str]:
        """
        Gets the fallback chain for a given model from the configuration.
        """
        chain = self.llm_config.router_fallback_chains.get(primary_model, [])
        return [primary_model] + chain

    def _parse_router_response(self, response_content: str) -> RouterAnalysis:
        """
        Parses the JSON response from the router LLM into a `RouterAnalysis` object.
        """
        try:
            # Use regex to find the JSON block
            json_match = re.search(r'\{[\s\S]*\}', response_content)
            if not json_match:
                print(f"   Failed to find JSON in router response.")
                return self._create_fallback_plan()

            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Handle cases where the response is nested under a key
            if "document_analysis" in data:
                data = data["document_analysis"]
            
            return RouterAnalysis(
                page_complexity=data.get('page_complexity', 'moderate'),
                has_dense_table=data.get('content_analysis', {}).get('has_dense_table', False),
                table_info=data.get('content_analysis', {}).get('table_info'),
                text_sections=data.get('content_analysis', {}).get('text_sections', {}),
                visual_elements=data.get('content_analysis', {}).get('visual_elements', {}),
                extraction_plans=[ExtractionPlan(**p) for p in data.get('extraction_plans', [])],
                total_estimated_tokens=data.get('total_estimated_tokens', 10000),
                warnings=data.get('warnings', [])
            )
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"   Failed to parse router response: {e}")
            return self._create_fallback_plan()

    def _create_fallback_plan(self) -> RouterAnalysis:
        """
        Creates a default, single-step extraction plan to be used when the
        router's LLM call fails completely.
        """
        return RouterAnalysis(
            page_complexity="unknown",
            has_dense_table=False,
            table_info=None,
            text_sections={},
            visual_elements={},
            extraction_plans=[
                ExtractionPlan(
                    step=1,
                    description="Fallback: Comprehensive extraction",
                    strategy=ExtractionStrategy.COMPREHENSIVE,
                    max_tokens=20000,
                )
            ],
            total_estimated_tokens=20000,
            warnings=["Router failed, using fallback plan."],
        )
