"""
This module implements the "minimal" extraction strategy.

The minimal strategy is designed for speed and efficiency. It extracts only
the most basic information from a page, such as the main title, a brief
summary, and the presence of tables.
"""
import base64
from backend.config.prompt_templates import get_extraction_prompt
from backend.core.interfaces import PageData
from backend.models.extraction import ExtractionPlan, ExtractionStrategy
from backend.strategies.base import BaseStrategy
from backend.strategies.factory import register_strategy
from backend.config.pipeline_config import PipelineConfig

class MinimalStrategy(BaseStrategy):
    """
    A strategy for performing a minimal extraction of basic information from a page.
    """

    def _create_content(self, page_data: PageData, plan: ExtractionPlan, config: PipelineConfig) -> list:
        """
        Prepares the content payload for the LLM API call.
        """
        prompt = get_extraction_prompt(
            ExtractionStrategy.MINIMAL,
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
        return content

register_strategy("minimal", MinimalStrategy)