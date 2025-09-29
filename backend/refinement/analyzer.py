"""
This module contains the logic for analyzing initial extraction results
to decide if a refinement step (e.g., a second, more focused extraction)
is necessary.
"""
import statistics
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import hashlib

@dataclass
class RefinementDecision:
    """
    A data class to hold the outcome of the refinement analysis.

    Attributes:
        should_refine: A boolean indicating whether a refinement is needed.
        target_section_id: The ID of the text block to be replaced.
        strategy: The suggested strategy for the refinement extraction.
    """
    should_refine: bool = False
    target_section_id: Optional[str] = None
    strategy: Optional[str] = "TABLE_FOCUS"

class RefinementAnalyzer:
    """
    Analyzes the output of an initial extraction to find areas for improvement.

    This class uses a set of heuristics to detect common extraction errors,
    such as tables that were misidentified as plain text. If such an error is
    found, it recommends a secondary, more focused extraction.
    """

    # Heuristic Parameters
    MIN_CONTENT_LENGTH = 500  # Minimum characters in a section to be considered.
    MIN_LINE_COUNT = 5          # Minimum number of lines to be considered a table.
    NUMERIC_DENSITY_THRESHOLD = 0.2  # More than 20% of chars should be numeric.
    LINE_LENGTH_VARIANCE_THRESHOLD = 0.5  # Low variance in line length is a table indicator.

    def _is_likely_table(self, text: str) -> bool:
        """
        Applies a set of heuristics to determine if a text block is likely a table.
        """
        if not isinstance(text, str) or len(text) < self.MIN_CONTENT_LENGTH:
            return False

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) < self.MIN_LINE_COUNT:
            return False

        # Heuristic 1: High density of numerical characters
        numeric_chars = sum(c.isdigit() for c in text)
        numeric_density = numeric_chars / len(text)
        
        # Heuristic 2: Low variance in line length
        line_lengths = [len(line) for line in lines]
        mean_len = statistics.mean(line_lengths)
        if mean_len == 0: return False
        variance = statistics.variance(line_lengths, mean_len) / mean_len
        
        # Heuristic 3: Presence of common separators (e.g., multiple spaces)
        separator_lines = sum(1 for line in lines if '  ' in line or '\t' in line)
        separator_ratio = separator_lines / len(lines)

        # Decision logic: A combination of factors suggests a table.
        numeric_condition = numeric_density > self.NUMERIC_DENSITY_THRESHOLD
        variance_condition = variance < self.LINE_LENGTH_VARIANCE_THRESHOLD
        separator_condition = separator_ratio > 0.6 # Most lines should have separators

        # A strong signal is low variance plus either numbers or separators.
        if variance_condition and (numeric_condition or separator_condition):
            return True
            
        return False

    def analyze_for_missed_tables(
        self, initial_result: Dict[str, Any]
    ) -> RefinementDecision:
        """
        Analyzes an initial extraction result to find missed tables.

        This method iterates through the text sections of an extraction result
        and applies heuristics to identify any that are likely tables.

        Args:
            initial_result: The dictionary representing the JSON output from
                               the first extraction pass.

        Returns:
            A `RefinementDecision` object indicating whether a secondary
            extraction should be triggered.
        """
        key_sections = initial_result.get("key_sections", [])
        if not isinstance(key_sections, list):
            return RefinementDecision(should_refine=False)

        for i, section in enumerate(key_sections):
            content = section.get("content", "")
            
            # Generate a stable ID for the section to target it for replacement
            section_id = hashlib.md5(json.dumps(section, sort_keys=True).encode()).hexdigest()
            initial_result["key_sections"][i]["section_id"] = section_id

            if self._is_likely_table(content):
                return RefinementDecision(
                    should_refine=True,
                    target_section_id=section_id
                )
        
        return RefinementDecision(should_refine=False)

import json