"""
Abstract interfaces for the core components of the extraction pipeline.

This module defines the contracts that concrete implementations of routers,
extractors, and mergers must adhere to. This supports the extensibility goal
of the project, allowing for new document types (e.g., DOCX, HTML) to be
supported by creating new adapters that implement these interfaces.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from backend.models.extraction import (
    ExtractionPlan,
    RouterAnalysis,
    ExtractionResult,
)
from backend.utils.document_parser import PageData

class IAsyncRouter(ABC):
    """
    Interface for a router that analyzes a page and creates an extraction plan.
    
    The router is the "brain" of the pipeline, responsible for deciding the
    most effective strategy for extracting data from a given page.
    """
    @abstractmethod
    async def analyze_page(
        self, page_data: PageData, config: Any
    ) -> RouterAnalysis:
        """
        Analyzes a single page and returns a plan for extraction.

        Args:
            page_data: The data of the page to analyze.
            config: The configuration for the router.

        Returns:
            A `RouterAnalysis` object containing the extraction plan.
        """
        pass

class IAsyncExtractor(ABC):
    """
    Interface for an extractor that executes a single step of an extraction plan.
    
    The extractor is responsible for taking a plan from the router and
    performing the actual data extraction using an LLM.
    """
    @abstractmethod
    async def execute_plan(
        self, plan: ExtractionPlan, page_data: PageData, config: Any
    ) -> ExtractionResult:
        """
        Executes a single step of an extraction plan.

        Args:
            plan: The `ExtractionPlan` to execute.
            page_data: The data of the page to extract from.
            config: The configuration for the extractor.

        Returns:
            An `ExtractionResult` object with the extracted data.
        """
        pass

class IResultMerger(ABC):
    """
    Interface for a merger that consolidates extraction results.
    
    The merger takes the outputs from multiple extraction steps and combines
    them into a single, coherent representation of the page's content.
    """
    @abstractmethod
    def merge_results(
        self,
        results: List[ExtractionResult],
        analysis: RouterAnalysis,
        raw_text: str,
    ) -> Dict[str, Any]:
        """
        Merges the results of multiple extraction steps into a single object.

        Args:
            results: A list of `ExtractionResult` objects.
            analysis: The `RouterAnalysis` object for the page.
            raw_text: The raw text of the page for fallback purposes.

        Returns:
            A dictionary containing the merged extraction results.
        """
        pass
