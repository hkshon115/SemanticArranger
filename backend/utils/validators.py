"""
This module contains various validation and parsing utilities.

These utilities are used to ensure data integrity and to robustly parse
and clean data from various sources, such as LLM responses and input files.
"""
import re
import json
import os
from typing import Optional, Dict, Any
import fitz  # PyMuPDF

class PDFValidator:
    """
    A utility for validating PDF files before processing.
    """

    def __init__(self, file_path: str, max_size_mb: int = 100):
        self.file_path = file_path
        self.max_size_mb = max_size_mb

    def validate(self) -> Optional[str]:
        """
        Performs all validation checks on the PDF file.
        Returns an error message string if validation fails, otherwise None.
        """
        error = self._check_existence_and_size()
        if error:
            return error
        
        error = self._check_corruption()
        if error:
            return error
            
        return None

    def _check_existence_and_size(self) -> Optional[str]:
        """Checks if the file exists and is within the size limit."""
        if not os.path.exists(self.file_path):
            return f"File not found: {self.file_path}"
        
        if not os.path.isfile(self.file_path):
            return f"Path is not a file: {self.file_path}"
            
        file_size_mb = os.path.getsize(self.file_path) / (1024 * 1024)
        if file_size_mb == 0:
            return "File is empty."
        
        if file_size_mb > self.max_size_mb:
            return f"File size ({file_size_mb:.2f} MB) exceeds the limit of {self.max_size_mb} MB."
            
        return None

    def _check_corruption(self) -> Optional[str]:
        """
        Performs a basic check for PDF corruption by trying to open it.
        """
        try:
            doc = fitz.open(self.file_path)
            if len(doc) == 0:
                return "PDF has no pages."
            doc.close()
        except Exception as e:
            return f"Failed to open PDF, it may be corrupted: {e}"
        return None

def parse_extraction_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Parse and validate extraction response with robust handling for common issues.
    """
    if not response_text:
        return None

    try:
        cleaned = response_text.strip()

        # Remove common thinking/control tags from models
        patterns_to_remove = [
            r"<ctrl\d+>thought.*?</ctrl\d+>",
            r"<ctrl\d+>.*?</ctrl\d+>",
            r"<thinking>.*?</thinking>",
            r"<reasoning>.*?</reasoning>",
            r"<process>.*?</process>",
            r"</?ctrl\d+>",
        ]
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)

        cleaned = cleaned.strip()

        # Handle markdown code blocks
        if "```json" in cleaned:
            match = re.search(r"```json\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
        elif "```" in cleaned:
            match = re.search(r"```\s*(.*?)\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

        # Attempt direct parsing
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fallback: find the first '{' and its matching '}'
        first_brace = cleaned.find("{")
        if first_brace != -1:
            last_brace = _find_matching_brace(cleaned, first_brace)
            if last_brace != -1:
                potential_json = cleaned[first_brace : last_brace + 1]
                try:
                    # Clean up common JSON errors like trailing commas
                    potential_json = re.sub(r",\s*}", "}", potential_json)
                    potential_json = re.sub(r",\s*]", "]", potential_json)
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    pass
        
        return None

    except Exception:
        return None

def _find_matching_brace(text: str, start_pos: int) -> int:
    """
    Find the matching closing brace for an opening brace, ignoring braces inside strings.
    """
    if start_pos >= len(text) or text[start_pos] != "{":
        return -1

    count = 0
    in_string = False
    escape_next = False

    for i in range(start_pos, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if not in_string:
            if char == "{":
                count += 1
            elif char == "}":
                count -= 1
                if count == 0:
                    return i
    return -1

def detect_legal_financial_content(page_text: str) -> bool:
    """Detect if content is likely legal/financial (high RECITATION risk)"""
    if not page_text:
        return False
        
    legal_financial_indicators = [
        # SEC filing indicators
        "form 10-k", "form 10-q", "form 8-k", "proxy statement",
        "annual report", "quarterly report", "item 1", "item 2", "item 3",
        
        # Legal document indicators
        "pursuant to", "securities act", "exchange act", "hereby certifies",
        "gaap", "non-gaap", "forward-looking statements", "safe harbor",
        
        # Financial terms that suggest reports
        "accounts receivable", "allowance for credit losses",
        "consolidated financial statements", "cash flows",
        "balance sheet", "income statement", "stockholders equity",
        
        # Risk disclosures (very common in 10-K/10-Q)
        "risk factors", "operations risks", "credit risk", "liquidity risk",
        "market risk", "operational risk", "compliance risk",
        
        # Privacy law indicators
        "ccpa", "gdpr", "cpra", "vcdpa", "privacy act",
        "data protection", "consumer privacy", "privacy law"
    ]
    
    text_lower = page_text.lower() if page_text else ""
    matches = sum(1 for indicator in legal_financial_indicators if indicator in text_lower)
    
    # If we find 3+ indicators, it's likely legal/financial content
    return matches >= 3