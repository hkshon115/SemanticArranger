"""
This module implements the "comprehensive" extraction strategy.

The comprehensive strategy is designed for dense, complex pages. It aims to
extract a wide range of information, including detailed summaries, all key
sections, insights from visual elements, and metadata.
"""
import base64
from typing import cast
from backend.config.prompt_templates import get_extraction_prompt
from backend.core.interfaces import PageData
from backend.models.extraction import ExtractionPlan, ExtractionStrategy
from backend.strategies.base import BaseStrategy
from backend.strategies.factory import register_strategy
from backend.config.pipeline_config import PipelineConfig

class ComprehensiveStrategy(BaseStrategy):
    """
    A strategy for performing a comprehensive extraction of detailed information from a page.
    """

    def _create_content(self, page_data: PageData, plan: ExtractionPlan, config: PipelineConfig) -> list:
        """
        Prepares the content payload for the LLM API call.
        """
        prompt = get_extraction_prompt(
            ExtractionStrategy.COMPREHENSIVE,
            plan.special_instructions,
            config.key_lang,
        )
        
        image_bytes = page_data.get_image()
        
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": base64.b64encode(image_bytes if image_bytes else b"").decode("utf-8"),
                },
            },
        ]
        
        # Add text context for comprehensive strategies
        page_text = page_data.get_text()
        if page_text and len(page_text) > 0:
            text_limit = 2000
            text_excerpt = page_text[:text_limit]
            if len(page_text) > text_limit:
                text_excerpt += "...[truncated]"
            cast(dict, content[0])["text"] += f"\n\nText excerpt:\n{text_excerpt}"
            
        return content

register_strategy("comprehensive", ComprehensiveStrategy)