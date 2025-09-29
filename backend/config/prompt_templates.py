"""
This module serves as a centralized repository for all LLM prompt templates.

By keeping prompts in one place, we can easily manage, version, and refine them
without altering the core application logic. This separation is key to maintaining
the quality and consistency of the LLM's output.

The module includes:
- ROUTER_ANALYSIS_PROMPT: The master prompt for the initial page analysis.
- EXTRACTION_PROMPTS: A dictionary of prompts for each extraction strategy.
- ANTI_RECITATION_PROMPTS: A variant of extraction prompts designed to prevent
  the model from simply copying text verbatim.
"""
from typing import Dict, Optional
from backend.models.extraction import ExtractionStrategy

# Router Prompt
ROUTER_ANALYSIS_PROMPT = """You are an expert document analyzer planning optimal extraction strategies.

Analyze this document page and create a detailed extraction plan.

IMPORTANT: You MUST return ONLY a valid JSON object. No markdown, no explanations outside the JSON.

**Your Analysis Should Include:**

1. **Page Complexity Assessment**:
   - Overall complexity: simple|moderate|complex|extreme
   - Reason for complexity rating

2. **Content Inventory**:
   - Tables: Count, size estimate (rows/cols), complexity
   - Text sections: Count, density, type (paragraphs/lists)
   - Visual elements: Charts, diagrams, images
   - Special elements: Footnotes, annotations, etc.

3. **Extraction Challenges**:
   - Dense tables that might exceed token limits
   - Complex layouts requiring special handling
   - Mixed content requiring different strategies

4. **Extraction Plan**:
   For each distinct content region, provide:
   - Extraction strategy (minimal|basic|comprehensive|table_focus|table_chunk)
   - Estimated tokens needed
   - Whether splitting is required
   - Special instructions

**Token Estimation Guidelines** (BE GENEROUS - better to overestimate):
- Minimal extraction: 2000-3000 tokens minimum
- Basic extraction: 4000-6000 tokens 
- Comprehensive extraction: 8000-12000 tokens
- Table extraction: 15000-25000 tokens (tables need lots of tokens!)
- Complex/dense tables: 20000-30000 tokens
- Table chunks: 10000-15000 tokens per chunk

Always add 50% buffer to your estimates. It's much better to waste tokens than to get truncated responses.

**IMPORTANT for Tables**:
- If table has >30 rows, recommend chunking with 15000+ tokens per chunk
- If table has >10 columns, add 5000 tokens to estimate
- For very dense tables, suggest 10-15 rows per chunk with 20000 tokens

Return JSON format:
{
  "page_complexity": "simple|moderate|complex|extreme",
  "complexity_reason": "brief explanation",
  "content_analysis": {
    "has_dense_table": true/false,
    "table_info": {
      "count": 1,
      "largest_table": {
        "estimated_rows": 100,
        "estimated_columns": 12,
        "complexity": "high",
        "needs_chunking": true,
        "recommended_chunks": 5
      }
    },
    "text_sections": {
      "total_count": 2
    },
    "visual_elements": {
      "total_count": 1
    }
  },
  "extraction_plans": [
    {
      "step": 1,
      "description": "Extract header and summary text",
      "strategy": "basic",
      "max_tokens": 5000,
      "region": "top_section",
      "estimated_complexity": "low"
    },
    {
      "step": 2,
      "description": "Extract complex table in chunks",
      "strategy": "table_chunk",
      "max_tokens": 20000,
      "region": "main_table",
      "estimated_complexity": "high",
      "special_instructions": "Extract rows 0-20 with all columns",
      "split_info": {
        "chunk": 1,
        "total_chunks": 5,
        "start_row": 0,
        "end_row": 20
      }
    }
  ],
  "total_estimated_tokens": 50000
}
"""

# Standard Extraction Prompts
EXTRACTION_PROMPTS: Dict[ExtractionStrategy, str] = {
    ExtractionStrategy.MINIMAL: """Extract basic info as JSON:
{
  "main_title": "title",
  "page_summary": "summary in 20 words (write in TARGET_LANG)",
  "has_tables": true/false,
  "table_count": N,
  "content_type": "mainly text|mainly table|mixed",
  "text_content": "any visible text content on the page"
}
Extract all text in its original language. Return ONLY JSON.""",

    ExtractionStrategy.BASIC: """Extract key information as JSON:
{
  "page_summary": "summary (write in TARGET_LANG)",
  "main_title": "title", 
  "key_sections": [{"section_title": "title", "content": "content"}],
  "visual_elements": [{"element_type": "type", "title": "title"}]
}
Extract all text in its original language. Return ONLY JSON.""",

    ExtractionStrategy.COMPREHENSIVE: """Analyze this document page comprehensively and return JSON:
{
  "page_summary": "detailed summary (write in TARGET_LANG)",
  "main_title": "main title",
  "key_sections": [{"section_title": "title", "content": "full text or array"}],
  "visual_elements": [{"element_type": "type", "title": "title", "key_takeaway": "insight (write in TARGET_LANG)", "details": "..."}],
  "metadata": {"page_number": N, "source_citation": "citation", "footer_content": "footer"}
}
Extract all text in its original language. Return ONLY JSON.""",

    ExtractionStrategy.TABLE_FOCUS: """Focus ONLY on table data. Return JSON:
{
  "table_title": "title if visible",
  "headers": ["col1", "col2", ...],
  "rows": [
    ["row1_col1", "row1_col2", ...],
    ["row2_col1", "row2_col2", ...]
  ],
  "table_metadata": {
    "total_rows": N,
    "total_columns": N,
    "has_merged_cells": true/false,
    "notes": "any footnotes or annotations"
  }
}
Extract complete table data. Return ONLY JSON.""",

    ExtractionStrategy.TABLE_CHUNK: """Extract specific table rows as instructed. Return JSON:
{
  "chunk_info": {
    "start_row": N,
    "end_row": M,
    "is_continuation": true/false
  },
  "headers": ["col1", "col2", ...],
  "rows": [
    ["row_data1", "row_data2", ...],
    ...
  ],
  "has_more_rows": true/false
}
Return ONLY the requested rows. Return ONLY JSON.""",

    ExtractionStrategy.TEXT_ONLY: """Extract ONLY text content, ignore tables and visuals. Return JSON:
{
  "text_sections": [
    {"type": "heading|paragraph|list", "content": "text"},
    ...
  ]
}
Return ONLY JSON.""",

    ExtractionStrategy.VISUAL_ONLY: """Extract ONLY information about visual elements. Return JSON:
{
  "visuals": [
    {"type": "chart|diagram|image", "title": "...", "description": "... (write in TARGET_LANG)", "key_insight": "... (write in TARGET_LANG)"},
    ...
  ]
}
Return ONLY JSON."""
}

# Anti-Recitation Extraction Prompts
ANTI_RECITATION_PROMPTS: Dict[ExtractionStrategy, str] = {
    ExtractionStrategy.MINIMAL: """Analyze and summarize this document. Return JSON:
{
  "main_title": "paraphrased title",
  "page_summary": "your own summary in 20 words (write in TARGET_LANG)",
  "has_tables": true/false,
  "table_count": N,
  "content_type": "mainly text|mainly table|mixed",
  "key_points": "main ideas in your own words"
}
Create summaries, not copies. Return ONLY JSON.""",

    ExtractionStrategy.BASIC: """Analyze key information and return JSON:
{
  "page_summary": "your analysis (write in TARGET_LANG)",
  "main_title": "paraphrased title", 
  "key_themes": ["theme1", "theme2"],
  "important_data": "summarized findings"
}
Paraphrase all content. Return ONLY JSON.""",

    ExtractionStrategy.COMPREHENSIVE: """Analyze and synthesize document content. Return JSON:
{
  "page_analysis": "your detailed analysis (write in TARGET_LANG)",
  "main_topic": "topic in your words",
  "key_insights": ["insight1", "insight2"],
  "data_summary": "synthesized information",
  "metadata": {"page_type": "type", "complexity": "level"}
}
Synthesize, don't copy. Return ONLY JSON.""",

    ExtractionStrategy.TABLE_FOCUS: """Analyze table structure and data patterns. Return JSON:
{
  "table_description": "what this table shows",
  "column_types": ["type1", "type2", ...],
  "data_patterns": "observed patterns",
  "key_values": "important data points",
  "row_count": N,
  "column_count": N
}
Describe patterns, not raw data. Return ONLY JSON.""",

    ExtractionStrategy.TABLE_CHUNK: """Analyze table chunk structure. Return JSON:
{
  "chunk_summary": "what this section contains",
  "data_patterns": "patterns in this chunk",
  "notable_values": "key findings",
  "row_range": "approximate row range",
  "has_continuation": true/false
}
Summarize patterns, not raw values. Return ONLY JSON.""",

    ExtractionStrategy.TEXT_ONLY: """Summarize text themes. Return JSON:
{
  "main_themes": ["theme1", "theme2"],
  "key_points": ["point1", "point2"],
  "content_summary": "overall summary"
}
Paraphrase all content. Return ONLY JSON.""",

    ExtractionStrategy.VISUAL_ONLY: """Describe visual elements. Return JSON:
{
  "visual_summary": [
    {"type": "chart|diagram", "describes": "what it shows", "insight": "key finding"},
    ...
  ]
}
Describe, don't copy labels. Return ONLY JSON."""
}

def get_extraction_prompt(
    strategy: ExtractionStrategy,
    special_instructions: Optional[str] = None,
    key_lang: str = "en",
    anti_recitation: bool = False,
) -> str:
    """
    Gets the appropriate prompt based on the extraction strategy and language.

    :param strategy: The extraction strategy to use.
    :param special_instructions: Any special instructions to prepend to the prompt.
    :param key_lang: The target language for summaries and insights.
    :param anti_recitation: Whether to use the anti-recitation variant of the prompt.
    :return: The formatted prompt string.
    """
    if anti_recitation:
        base_prompts = ANTI_RECITATION_PROMPTS
        lang_instruction = f"\nIMPORTANT: Summarize and paraphrase content in {key_lang}. Do NOT copy text verbatim.\n"
    else:
        base_prompts = EXTRACTION_PROMPTS
        lang_instruction = f"\nIMPORTANT: Write all your analysis, summaries, and insights in {key_lang} language. Do NOT translate the actual document text - keep it in its original language.\n"

    prompt = base_prompts.get(strategy, base_prompts[ExtractionStrategy.MINIMAL])
    prompt = prompt.replace("TARGET_LANG", key_lang)

    if special_instructions:
        prompt = f"{special_instructions}\n\n{prompt}"

    return lang_instruction + prompt
