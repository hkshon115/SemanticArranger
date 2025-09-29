"""
This module implements the "table_chunk" extraction strategy.

This strategy is used for extracting a specific range of rows from a large
table that might otherwise exceed the token limit of the LLM. It is typically
used in conjunction with the `table_focus` strategy.
"""
import base64
from backend.config.prompt_templates import get_extraction_prompt
from backend.core.interfaces import PageData
from backend.models.extraction import ExtractionPlan, ExtractionStrategy
from backend.strategies.base import BaseStrategy
from backend.strategies.factory import register_strategy
from backend.config.pipeline_config import PipelineConfig

class TableChunkStrategy(BaseStrategy):
    """
    A strategy for extracting a specific chunk of a large table from a page.
    """

    def _create_content(self, page_data: PageData, plan: ExtractionPlan, config: PipelineConfig) -> list:
        """
        Prepares the content payload for the LLM API call.
        """
        prompt = get_extraction_prompt(
            ExtractionStrategy.TABLE_CHUNK,
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

register_strategy("table_chunk", TableChunkStrategy)