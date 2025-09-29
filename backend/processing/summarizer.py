import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.llm_app.async_client import AsyncLLMClient
from backend.config.pipeline_config import PipelineConfig
from backend.utils.validators import parse_extraction_response

class Summarizer:
    """
    Generates an executive summary and key takeaways from the extracted content
    of a document.
    """

    def __init__(self, client: AsyncLLMClient):
        """
        Initializes the Summarizer.

        Args:
            client: An instance of `AsyncLLMClient` for making API calls.
        """
        self.client = client

    def _prepare_content_for_summary(self, extraction_results: List[Dict]) -> str:
        """
        Prepares a condensed string representation of the document's content
        to be used as context for the summarization prompt.
        """
        content_parts = [f"DOCUMENT OVERVIEW:\n- Total pages: {len(extraction_results)}\n"]
        for idx, page in enumerate(extraction_results, 1):
            page_content = [f"\n=== PAGE {page.get('metadata', {}).get('page_number', idx)} ==="]
            if page.get("main_title"):
                page_content.append(f"Title: {page['main_title']}")
            if page.get("page_summary"):
                page_content.append(f"Summary: {page['page_summary']}")
            content_parts.extend(page_content)
        return "\n".join(content_parts)

    async def generate_summary(
        self,
        extraction_results: List[Dict],
        config: PipelineConfig,
        max_takeaways: int = 10,
        summarizer_llm_model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates an executive summary and key takeaways for the document.

        This method calls an LLM with the condensed content of the document
        and structures the response. It includes a fallback mechanism to
        provide a basic summary if the LLM call fails.

        Args:
            extraction_results: A list of dictionaries representing the
                                extracted content for each page.
            config: The pipeline configuration object.
            max_takeaways: The maximum number of key takeaways to generate.
            summarizer_llm_model: (Optional) The specific LLM to use for
                                summarization.

        Returns:
            A dictionary containing the executive summary and other metadata.
        """
        prepared_content = self._prepare_content_for_summary(extraction_results)
        
        lang_instructions = {
            "en": "Please provide the summary and takeaways in English.",
            "ko": "요약과 핵심 내용을 한국어로 제공해 주세요.",
        }
        lang_instruction = lang_instructions.get(config.key_lang, lang_instructions["en"])

        prompt = f"""You are an expert document analyst. Analyze the following document content and provide a comprehensive executive summary.

{prepared_content}

Please provide:
1. **EXECUTIVE SUMMARY** (2-3 paragraphs)
2. **KEY TAKEAWAYS** (up to {max_takeaways} points)
3. **DOCUMENT METADATA** (document_type, primary_subject, etc.)

{lang_instruction}

Format your response as JSON with the structure:
{{
  "executive_summary": "...",
  "key_takeaways": [{{"point": "...", "importance": "high/medium/low"}}],
  "document_metadata": {{"document_type": "...", "primary_subject": "..."}}
}}
"""
        model = summarizer_llm_model or config.summarization_model
        try:
            response = await self.client.chat(
                model=model,
                content=prompt,
                system="You are a professional document analyst. Always respond with valid JSON.",
                max_tokens=4000,
                temperature=0.3,
            )

            if response.get("error"):
                return self._create_fallback_summary(extraction_results, response["error"])

            summary_data = parse_extraction_response(response.get("content", ""))
            if not summary_data:
                return self._create_fallback_summary(extraction_results, "Failed to parse JSON response.")

            summary_data["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "model_used": model,
                "language": config.key_lang,
            }
            return summary_data

        except Exception as e:
            return self._create_fallback_summary(extraction_results, str(e))

    def _create_fallback_summary(
        self, extraction_results: List[Dict], error_msg: str
    ) -> Dict[str, Any]:
        """
        Creates a basic, fallback summary when the primary summarization fails.
        """
        return {
            "executive_summary": "Summary generation failed.",
            "key_takeaways": [
                {"point": page.get("page_summary", "")[:200]}
                for page in extraction_results[:5]
                if page.get("page_summary")
            ],
            "document_metadata": {},
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "error": error_msg,
                "fallback_used": True,
            },
        }
