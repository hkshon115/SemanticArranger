import asyncio
from typing import List, Dict, Any
import fitz  # PyMuPDF

from backend.core.interfaces import IAsyncRouter, IAsyncExtractor, IResultMerger
from backend.config.pipeline_config import PipelineConfig
from backend.utils.document_parser import PageData
from backend.utils.rate_limiter import RateLimiter
from backend.refinement.analyzer import RefinementAnalyzer
from backend.models.extraction import ExtractionPlan, ExtractionStrategy, ExtractionResult

class ParallelProcessor:
    """
    Processes the pages of a document in parallel.

    This class manages the concurrency of page processing, using a semaphore
    to limit the number of pages being processed at any given time. It is
    responsible for orchestrating the router-extractor-merger sequence for
    each page.
    """

    def __init__(
        self,
        router: IAsyncRouter,
        extractor: IAsyncExtractor,
        merger: IResultMerger,
        rate_limiter: RateLimiter,
    ):
        """
        Initializes the ParallelProcessor.

        Args:
            router: An instance of a class that implements `IAsyncRouter`.
            extractor: An instance of a class that implements `IAsyncExtractor`.
            merger: An instance of a class that implements `IResultMerger`.
            rate_limiter: An instance of `RateLimiter` to control API call frequency.
        """
        self.router = router
        self.extractor = extractor
        self.merger = merger
        self.rate_limiter = rate_limiter
        self.analyzer = RefinementAnalyzer()

    async def _process_single_page(
        self, page_num: int, page: fitz.Page, semaphore: asyncio.Semaphore, config: PipelineConfig
    ) -> Dict[str, Any]:
        """
        The core processing logic for a single page.

        This method is wrapped by a semaphore to control concurrency. It performs
        the analysis, extraction, and refinement for a single page.

        Args:
            page_num: The page number being processed.
            page: The `fitz.Page` object.
            semaphore: The asyncio semaphore for concurrency control.
            config: The pipeline configuration.

        Returns:
            A dictionary containing the final, merged extraction result for the page.
        """
        async with semaphore:
            async with self.rate_limiter:
                print(f"Starting processing for page {page_num}...")
                
                page_data = PageData(page_num=page_num, page=page)
                
            # Step 1: Initial analysis and extraction
            router_analysis = await self.router.analyze_page(
                page_data, config.key_lang
            )
            extraction_results = []
            for plan in router_analysis.extraction_plans:
                try:
                    result = await self.extractor.execute_plan(plan, page_data, config.key_lang)
                    extraction_results.append(result)
                except Exception as e:
                    print(f"Extraction failed for page {page_num}, step {plan.step}: {e}")
                    error_result = ExtractionResult(
                        step=plan.step,
                        strategy=plan.strategy.value,
                        success=False,
                        content=None,
                        error=str(e)
                    )
                    extraction_results.append(error_result)

            # Step 2: Initial merge of results
            initial_merged_result = self.merger.merge_results(
                extraction_results, router_analysis, page_data.get_text(), page_num=page_num
            )

            # Step 3: Iterative Refinement (if enabled)
            if config.iterative_refinement_enabled:
                decision = self.analyzer.analyze_for_missed_tables(initial_merged_result)
                if decision.should_refine:
                    print(f"Refining page {page_num} for missed table...")
                    
                    # Create a new plan for the focused extraction
                    refinement_plan = ExtractionPlan(
                        step=len(extraction_results) + 1,
                        description="Refinement: Focused table extraction",
                        strategy=ExtractionStrategy.TABLE_FOCUS,
                        max_tokens=20000, # Generous token limit for tables
                    )
                    
                    # Execute the refinement extraction
                    refined_result = await self.extractor.execute_plan(
                        refinement_plan, page_data, config.key_lang
                    )
                    
                    # Merge the refined result back into the initial result
                    final_result = self.merger.merge_refined_results(
                        initial_merged_result, refined_result, decision.target_section_id
                    )
                else:
                    final_result = initial_merged_result
            else:
                final_result = initial_merged_result
            
            print(f"Finished processing for page {page_num}.")
            return final_result

    async def process_document(
        self, pdf_path: str, config: PipelineConfig
    ) -> List[Dict[str, Any]]:
        """
        Processes a full PDF document in parallel.

        This method opens the PDF, creates a processing task for each page,
        and runs them concurrently using `asyncio.gather`.

        Args:
            pdf_path: The path to the input PDF file.
            config: The pipeline configuration.

        Returns:
            A list of dictionaries, where each dictionary is the final
            extraction result for a page.
        """
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)
        
        semaphore = asyncio.Semaphore(config.concurrency_limit)
        
        tasks = [
            self._process_single_page(i + 1, pdf_document[i], semaphore, config)
            for i in range(total_pages)
        ]

        processed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        pdf_document.close()

        final_results = []
        for i, result in enumerate(processed_results):
            if isinstance(result, Exception):
                print(f"An error occurred while processing page {i+1}: {result}")
            else:
                final_results.append(result)
        
        return final_results