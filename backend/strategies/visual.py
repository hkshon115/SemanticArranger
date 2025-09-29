"""
This module implements the "visual" extraction strategy.

This strategy is specialized for extracting information from visual elements
on a page, such as charts, graphs, and diagrams. It prompts the LLM to
describe the visual and extract key insights.
"""
import base64
from backend.config.prompt_templates import get_extraction_prompt
from backend.core.interfaces import PageData
from backend.models.extraction import ExtractionPlan, ExtractionStrategy
from backend.strategies.base import BaseStrategy
from backend.strategies.factory import register_strategy
from backend.config.pipeline_config import PipelineConfig

class VisualStrategy(BaseStrategy):
    """
    A strategy for focusing specifically on extracting visual element data from a page.
    """

    def _create_content(self, page_data: PageData, plan: ExtractionPlan, config: PipelineConfig) -> list:
        """
        Prepares the content payload for the LLM API call.
        """
        prompt = get_extraction_prompt(
            ExtractionStrategy.VISUAL_ONLY,
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

register_strategy("visual_only", VisualStrategy)