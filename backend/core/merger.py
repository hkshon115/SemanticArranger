"""
Core Merger Module for the Extraction Pipeline.

This module contains the ResultMerger, which is responsible for consolidating
the results from multiple extraction steps into a single, coherent document
page representation. It also handles deduplication and fallback to raw text
if all extractions fail.
"""
import hashlib
import json
from collections import defaultdict
from typing import List, Dict, Any, Optional

from backend.core.interfaces import IResultMerger
from backend.models.extraction import ExtractionResult, RouterAnalysis


class ResultMerger(IResultMerger):
    """
    Merges results from multiple extraction steps into a single, coherent
    representation of a page's content. This class includes logic for
    deduplication, handling different strategy outputs, and falling back to
    raw text if all extractions fail.
    """
    
    @staticmethod
    def _find_key_in_dict(data: Dict, target_keys: List[str], max_depth: int = 5) -> Any:
        """
        Recursively searches for a list of target keys in a nested dictionary.
        """
        if not isinstance(data, dict) or max_depth <= 0:
            return None
        
        # Check direct keys first
        for key in target_keys:
            if key in data:
                return data[key]
        
        # Search in nested dicts
        for value in data.values():
            if isinstance(value, dict):
                result = ResultMerger._find_key_in_dict(value, target_keys, max_depth - 1)
                if result:
                    return result
        return None
    
    @staticmethod
    def _extract_all_text(data: Any, max_depth: int = 5) -> str:
        """
        Extracts all text content from potentially nested data structures.
        """
        if max_depth <= 0:
            return ""
        
        texts = []
        
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            for key, value in data.items():
                if key not in ['metadata', 'headers', 'rows']:  # Skip structural elements
                    text = ResultMerger._extract_all_text(value, max_depth - 1)
                    if text:
                        texts.append(text)
        elif isinstance(data, list):
            for item in data:
                text = ResultMerger._extract_all_text(item, max_depth - 1)
                if text:
                    texts.append(text)
        
        return " ".join(texts).strip()
    
    @staticmethod
    def _normalize_content(content: Any) -> Dict:
        """
        Normalizes the content from an extraction result into a dictionary format.
        """
        if isinstance(content, dict):
            return content
        elif isinstance(content, list) and len(content) == 1:
            return ResultMerger._normalize_content(content[0])
        elif isinstance(content, str):
            # Try to parse as JSON
            try:
                return json.loads(content)
            except:
                return {"text_content": content}
        else:
            return {"raw_content": str(content)}
    
    @staticmethod
    def _process_by_strategy(result: ExtractionResult, merged: Dict) -> None:
        """
        Routes the extraction result to the appropriate processing method
        based on the strategy used.
        """
        content = ResultMerger._normalize_content(result.content)
        
        # Handle anti-recitation strategies
        base_strategy = result.strategy.replace("_anti_recitation", "")
        
        if base_strategy == "minimal":
            ResultMerger._process_minimal_extraction(content, merged)
        elif base_strategy == "basic":
            ResultMerger._process_basic_extraction(content, merged)
        elif base_strategy == "comprehensive":
            ResultMerger._process_comprehensive_extraction(content, merged)
        elif base_strategy in ["table_focus", "table_chunk"]:
            ResultMerger._process_table_extraction(content, merged)
        else:
            # Generic processing for unknown strategies
            ResultMerger._process_generic_extraction(content, merged)
    
    @staticmethod
    def _process_minimal_extraction(content: Dict, merged: Dict) -> None:
        """Processes results from the MINIMAL extraction strategy."""
        # Title extraction
        title_keys = ["main_title", "title", "document_title", "page_title", "main_topic"]
        title = ResultMerger._find_key_in_dict(content, title_keys)
        if title and not merged["main_title"]:
            merged["main_title"] = title
        
        # Summary extraction
        summary_keys = ["page_summary", "summary", "description", "abstract", "page_analysis"]
        summary = ResultMerger._find_key_in_dict(content, summary_keys)
        if summary and not merged["page_summary"]:
            merged["page_summary"] = summary
        
        # Text content or key points
        text_keys = ["text_content", "content", "body", "text", "key_points"]
        text = ResultMerger._find_key_in_dict(content, text_keys)
        if text:
            merged["key_sections"].append({
                "section_title": "Content",
                "content": text
            })
    
    @staticmethod
    def _process_basic_extraction(content: Dict, merged: Dict) -> None:
        """Processes results from the BASIC extraction strategy."""
        ResultMerger._extract_title_summary(content, merged)
        
        # Handle sections or themes
        section_keys = ["key_sections", "sections", "text_sections", "key_themes"]
        sections = ResultMerger._find_key_in_dict(content, section_keys)
        if sections and isinstance(sections, list):
            merged["key_sections"].extend(sections)
        
        # Handle summarized data
        if "important_data" in content:
            merged["key_sections"].append({
                "section_title": "Important Data",
                "content": content["important_data"]
            })
    
    @staticmethod
    def _process_comprehensive_extraction(content: Dict, merged: Dict) -> None:
        """Processes results from the COMPREHENSIVE extraction strategy."""
        ResultMerger._extract_title_summary(content, merged)
        ResultMerger._extract_sections(content, merged)
        ResultMerger._extract_visual_elements(content, merged)
        ResultMerger._extract_metadata(content, merged)
        
        # Handle insights from anti-recitation
        if "key_insights" in content:
            for insight in content["key_insights"]:
                merged["key_sections"].append({
                    "section_title": "Key Insight",
                    "content": insight
                })
    
    @staticmethod
    def _process_table_extraction(content: Dict, merged: Dict) -> None:
        """Processes results from table-focused extraction strategies."""
        # Handle regular table extraction
        if "headers" in content or "rows" in content:
            table_data = {
                "title": content.get("table_title", "Untitled Table"),
                "headers": content.get("headers", []),
                "rows": content.get("rows", []),
                "metadata": content.get("table_metadata", {})
            }
            
            if "chunk_info" in content:
                table_data["chunk_info"] = content["chunk_info"]
            
            merged["tables"].append(table_data)
        
        # Handle anti-recitation table analysis
        elif "table_description" in content or "data_patterns" in content:
            merged["key_sections"].append({
                "section_title": "Table Analysis",
                "content": {
                    "description": content.get("table_description", ""),
                    "patterns": content.get("data_patterns", ""),
                    "key_values": content.get("key_values", ""),
                    "notable_values": content.get("notable_values", "")
                }
            })
    
    @staticmethod
    def _process_generic_extraction(content: Dict, merged: Dict) -> None:
        """Provides generic processing for unknown or custom extraction strategies."""
        ResultMerger._extract_title_summary(content, merged)
        
        # Try to extract any structured content
        for key, value in content.items():
            if key in ["metadata", "extraction_details"]:
                continue
            
            if isinstance(value, str) and len(value) > 50:
                merged["key_sections"].append({
                    "section_title": key.replace("_", " ").title(),
                    "content": value
                })
            elif isinstance(value, list) and value:
                # Could be sections or other structured data
                if all(isinstance(item, dict) for item in value):
                    if "section_title" in value[0] or "title" in value[0]:
                        merged["key_sections"].extend(value)
    
    @staticmethod
    def _extract_title_summary(content: Dict, merged: Dict) -> None:
        """A helper to extract the main title and summary from a content dictionary."""
        if not merged["main_title"]:
            title_keys = ["main_title", "title", "document_title", "page_title", "main_topic"]
            title = ResultMerger._find_key_in_dict(content, title_keys)
            if title:
                merged["main_title"] = title
        
        if not merged["page_summary"]:
            summary_keys = ["page_summary", "summary", "description", "abstract", "page_analysis"]
            summary = ResultMerger._find_key_in_dict(content, summary_keys)
            if summary:
                merged["page_summary"] = summary
    
    @staticmethod
    def _extract_sections(content: Dict, merged: Dict) -> None:
        """A helper to extract key sections from a content dictionary."""
        # Direct sections
        if "key_sections" in content and isinstance(content["key_sections"], list):
            merged["key_sections"].extend(content["key_sections"])
        
        # Text content as dict
        if "text_content" in content and isinstance(content["text_content"], dict):
            for section_name, section_content in content["text_content"].items():
                if section_name not in ["metadata", "headers"]:
                    merged["key_sections"].append({
                        "section_title": section_name.replace("_", " ").title(),
                        "content": section_content
                    })
        
        # Data summary from anti-recitation
        if "data_summary" in content:
            merged["key_sections"].append({
                "section_title": "Data Summary",
                "content": content["data_summary"]
            })
    
    @staticmethod
    def _extract_visual_elements(content: Dict, merged: Dict) -> None:
        """A helper to extract visual elements from a content dictionary."""
        visual_keys = ["visual_elements", "visuals", "figures", "charts", "visual_summary"]
        visuals = ResultMerger._find_key_in_dict(content, visual_keys)
        if visuals and isinstance(visuals, list):
            merged["visual_elements"].extend(visuals)
    
    @staticmethod
    def _extract_metadata(content: Dict, merged: Dict) -> None:
        """A helper to extract metadata from a content dictionary."""
        if "metadata" in content and isinstance(content["metadata"], dict):
            for key, value in content["metadata"].items():
                if key not in merged["metadata"]:
                    merged["metadata"][key] = value
    
    @staticmethod
    def _deduplicate_content(merged: Dict) -> None:
        """Removes duplicate content from the merged result."""
        # Deduplicate sections
        seen_content = set()
        unique_sections = []
        for section in merged["key_sections"]:
            content_str = json.dumps(section, sort_keys=True)
            content_hash = hashlib.md5(content_str.encode()).hexdigest()
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_sections.append(section)
        merged["key_sections"] = unique_sections
        
        # Deduplicate visual elements
        seen_visuals = set()
        unique_visuals = []
        for visual in merged["visual_elements"]:
            visual_str = json.dumps(visual, sort_keys=True)
            visual_hash = hashlib.md5(visual_str.encode()).hexdigest()
            if visual_hash not in seen_visuals:
                seen_visuals.add(visual_hash)
                unique_visuals.append(visual)
        merged["visual_elements"] = unique_visuals
    
    @staticmethod
    def _validate_and_fallback(merged: Dict, extraction_results: List[ExtractionResult], 
                              router_analysis: RouterAnalysis, 
                              raw_page_text: Optional[str] = None) -> None:
        """
        Validates the merged results and falls back to raw text if no
        meaningful content was extracted.
        """
        
        # Check if we have any meaningful content
        has_content = any([
            merged["main_title"],
            merged["page_summary"],
            merged["key_sections"],
            merged["tables"],
            merged["visual_elements"]
        ])
        
        if not has_content:
            # Try to extract any text from successful extractions first
            all_text = []
            for result in extraction_results:
                if result.success and result.content:
                    text = ResultMerger._extract_all_text(result.content)
                    if text:
                        all_text.append(text)
            
            if all_text:
                combined_text = " ".join(all_text)
                # Use first line as title
                lines = combined_text.split('\n')
                merged["main_title"] = lines[0][:200] if lines else "Untitled"
                merged["page_summary"] = combined_text[:500] + "..." if len(combined_text) > 500 else combined_text
                merged["key_sections"].append({
                    "section_title": "Extracted Content",
                    "content": combined_text
                })
            elif raw_page_text:
                # ULTIMATE FALLBACK: Use raw PDF text
                print(f"   Using raw PDF text as fallback ({len(raw_page_text)} chars)")
                
                # Extract title from raw text
                lines = raw_page_text.split('\n')
                non_empty_lines = [line.strip() for line in lines if line.strip()]
                
                # Try to find a reasonable title
                title = "Untitled Page"
                if non_empty_lines:
                    # Use first non-empty line as title (max 200 chars)
                    title = non_empty_lines[0][:200]
                
                merged["main_title"] = title
                merged["page_summary"] = f"Raw text extraction ({len(raw_page_text)} characters)"
                
                # Add raw text to key_sections
                merged["key_sections"].append({
                    "section_title": "Raw PDF Content (Fallback)",
                    "content": raw_page_text,
                    "extraction_method": "raw_pdf_text",
                    "is_fallback": True
                })
                
                # Add metadata about fallback
                merged["metadata"]["extraction_fallback"] = "raw_pdf_text"
                merged["metadata"]["merge_warnings"] = ["All extraction methods failed, using raw PDF text"]
            else:
                # Last resort fallback (no text available)
                merged["main_title"] = f"Page (Complexity: {router_analysis.page_complexity})"
                merged["page_summary"] = f"Page extraction failed completely"
                merged["metadata"]["merge_warnings"] = ["No content could be extracted"]
  
    @staticmethod
    def _deduplicate_with_raw_text(merged: Dict) -> None:
        """
        An enhanced deduplication method that intelligently handles the
        presence of a raw text fallback.
        """
        
        # First, check if we have raw text fallback
        has_raw_fallback = False
        raw_content = ""
        
        for section in merged["key_sections"]:
            if section.get("is_fallback") and section.get("extraction_method") == "raw_pdf_text":
                has_raw_fallback = True
                raw_content = section.get("content", "")
                break
        
        if not has_raw_fallback:
            # Use existing deduplication
            ResultMerger._deduplicate_content(merged)
            return
        
        # If we have raw fallback, check for duplicates with other sections
        unique_sections = []
        seen_content = set()
        raw_text_needed = True  # Flag to determine if we need raw text
        
        for section in merged["key_sections"]:
            if section.get("is_fallback"):
                # Skip raw fallback for now, we'll add it at the end if needed
                continue
            
            # Check if this section's content is substantial
            section_content = section.get("content", "")
            
            if isinstance(section_content, str) and len(section_content) > 50:
                # We have substantial extracted content, might not need raw fallback
                raw_text_needed = False
            
            # Create content hash for deduplication
            content_str = json.dumps(section, sort_keys=True)
            content_hash = hashlib.md5(content_str.encode()).hexdigest()
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_sections.append(section)
        
        # Add raw text fallback only if needed
        if raw_text_needed and raw_content:
            # Check if raw content significantly differs from extracted content
            extracted_text = " ".join([
                str(s.get("content", "")) 
                for s in unique_sections 
                if s.get("content")
            ])
            
            # Simple overlap check (can be made more sophisticated)
            if len(extracted_text) < len(raw_content) * 0.5:
                # Extracted content is less than 50% of raw content, add raw as supplement
                unique_sections.append({
                    "section_title": "Additional Raw Content",
                    "content": raw_content,
                    "extraction_method": "raw_pdf_text",
                    "is_fallback": True
                })
                print(f"   Added raw PDF text to supplement extraction")
            else:
                print(f"   Skipped raw PDF text (sufficient extracted content)")        
        merged["key_sections"] = unique_sections
        
        # Continue with visual elements deduplication
        seen_visuals = set()
        unique_visuals = []
        for visual in merged["visual_elements"]:
            visual_str = json.dumps(visual, sort_keys=True)
            visual_hash = hashlib.md5(visual_str.encode()).hexdigest()
            if visual_hash not in seen_visuals:
                seen_visuals.add(visual_hash)
                unique_visuals.append(visual)
        merged["visual_elements"] = unique_visuals
       
    def merge_results(self, 
                     results: List[ExtractionResult], 
                     analysis: RouterAnalysis,
                     raw_text: Optional[str] = None,
                     page_num: int = 0) -> Dict[str, Any]:
        """
        Merges the results of multiple extraction steps into a single object,
        with support for raw text fallback.
        """
        
        merged = {
            "page_complexity": analysis.page_complexity,
            "extraction_method": "smart_routing",
            "total_steps": len(results),
            "successful_steps": sum(1 for r in results if r.success),
            "main_title": None,
            "page_summary": None,
            "key_sections": [],
            "visual_elements": [],
            "tables": [],
            "metadata": {
                "page_number": page_num,
                "router_warnings": analysis.warnings,
                "total_tokens_used": sum(r.tokens_used for r in results),
                "total_time": sum(r.time_elapsed for r in results),
                "extraction_details": [{
                    "step": r.step,
                    "strategy": r.strategy,
                    "success": r.success,
                    "tokens_used": r.tokens_used,
                    "time_elapsed": r.time_elapsed,
                    "error": r.error
                } for r in results],
                "extraction_strategies_used": list(set(r.strategy for r in results if r.success)),
                "processing_errors": [],
                "uses_anti_recitation": any("anti_recitation" in r.strategy for r in results if r.success)
            }
        }
        
        # Process each successful result
        for result in results:
            if not result.success or not result.content:
                continue
            
            try:
                self._process_by_strategy(result, merged)
            except Exception as e:
                merged["metadata"]["processing_errors"].append({
                    "step": result.step,
                    "strategy": result.strategy,
                    "error": str(e)
                })
        
        # Merge table chunks if needed
        merged["tables"] = self._merge_table_chunks(merged["tables"])
        
        # Validate and provide fallbacks (now with raw text)
        self._validate_and_fallback(merged, results, analysis, raw_text)
        
        # Deduplicate content (enhanced to handle raw text)
        self._deduplicate_with_raw_text(merged)
        
        return merged

    def merge_refined_results(
        self,
        initial_result: Dict,
        refined_result: ExtractionResult,
        target_section_id: str,
    ) -> Dict[str, Any]:
        """
        Merges a secondary, refined extraction result into an initial result.

        This is used by the refinement process to replace a text block that
        was misidentified as text with a properly extracted table.

        Args:
            initial_result: The result from the first broad extraction.
            refined_result: The result from the secondary, focused extraction.
            target_section_id: The ID of the text block to be replaced.

        Returns:
            The final, merged dictionary.
        """
        # If the secondary extraction failed or produced no content, return the original.
        if not refined_result.success or not refined_result.content:
            return initial_result

        new_tables = refined_result.content.get("tables", [])
        if not new_tables:
            return initial_result

        # Add the new table(s) to the initial result
        initial_result["tables"].extend(new_tables)

        # Remove the old text block that has now been correctly identified as a table
        initial_result["key_sections"] = [
            section
            for section in initial_result.get("key_sections", [])
            if section.get("section_id") != target_section_id
        ]

        return initial_result

    
    @staticmethod
    def _merge_table_chunks(tables: List[Dict]) -> List[Dict]:
        """
        Merges table chunks from multiple extraction steps into complete tables.
        """
        
        # Group tables by title
        table_groups = defaultdict(list)
        standalone_tables = []
        
        for table in tables:
            if "chunk_info" in table:
                table_groups[table["title"]].append(table)
            else:
                standalone_tables.append(table)
        
        # Merge chunks
        merged_tables = []
        for title, chunks in table_groups.items():
            # Sort by start row
            chunks.sort(key=lambda x: x.get("chunk_info", {}).get("start_row", 0))
            
            merged_table = {
                "title": title,
                "headers": chunks[0].get("headers", []) if chunks else [],
                "rows": [],
                "metadata": {
                    "merged_from_chunks": len(chunks),
                    "total_rows": 0
                }
            }
            
            for chunk in chunks:
                merged_table["rows"].extend(chunk.get("rows", []))
                
            merged_table["metadata"]["total_rows"] = len(merged_table["rows"])
            merged_tables.append(merged_table)
        
        return merged_tables + standalone_tables
