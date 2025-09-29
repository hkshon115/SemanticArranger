import asyncio
from typing import List, Dict, Any

from backend.config.llm_config import LLMConfig, load_llm_config
from backend.config.pipeline_config import PipelineConfig
from backend.llm_app.async_client import AsyncLLMClient
from backend.processing.chunker import Chunker
from backend.processing.parallel_processor import ParallelProcessor
from backend.processing.summarizer import Summarizer
from backend.core.router import AsyncRouter
from backend.core.extractor import AsyncExtractor
from backend.core.merger import ResultMerger
from backend.utils.rate_limiter import RateLimiter

class PipelineOrchestrator:
    """
    Orchestrates the entire document processing pipeline.

    This class initializes and wires together all the components of the pipeline,
    including the router, extractor, merger, chunker, and summarizer. It manages
    the end-to-end flow of processing a document asynchronously.
    """

    def __init__(self):
        """
        Initializes the PipelineOrchestrator.
        """
        self.client = AsyncLLMClient()
        self.llm_config = load_llm_config()
        self.router = AsyncRouter(self.client, self.llm_config)
        self.extractor = AsyncExtractor(self.client, self.llm_config)
        self.merger = ResultMerger()
        self.chunker = Chunker()
        self.summarizer = Summarizer(self.client)

    async def process_document_async(
        self, pdf_path: str, config: PipelineConfig, summarizer_llm_model: str = None
    ) -> Dict[str, Any]:
        """
        Orchestrates the asynchronous processing of a PDF document.

        This method manages the entire pipeline flow:
        1. Processes all pages in parallel to get extraction results.
        2. Generates an executive summary from the results.
        3. Chunks the extracted content for downstream tasks.

        Args:
            pdf_path: The path to the input PDF file.
            config: The pipeline configuration object.
            summarizer_llm_model: (Optional) The specific LLM to use for summarization.

        Returns:
            A dictionary containing the extraction results, summary, and chunks.
        """
        rate_limiter = RateLimiter(rate_limit=config.rate_limit_per_minute)
        
        parallel_processor = ParallelProcessor(
            router=self.router,
            extractor=self.extractor,
            merger=self.merger,
            rate_limiter=rate_limiter,
        )

        # Step 1: Process all pages in parallel to get extraction results
        extraction_results = await parallel_processor.process_document(pdf_path, config)

        # Step 2: Generate the executive summary from the extraction results
        summary_task = self.summarizer.generate_summary(
            extraction_results, config, summarizer_llm_model=summarizer_llm_model
        )
        
        # Step 3: Create chunks from the extraction results
        chunking_task = asyncio.to_thread(
            self.chunker.chunk_extraction_result, extraction_results
        )

        # Run summarization and chunking concurrently
        summary, chunks = await asyncio.gather(summary_task, chunking_task)

        return {
            "extraction_results": extraction_results,
            "executive_summary": summary,
            "chunks": chunks,
            "chunking_stats": self.chunker.get_chunking_stats(),
        }
