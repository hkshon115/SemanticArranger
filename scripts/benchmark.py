import asyncio
import os
import cProfile
import pstats
import tracemalloc
import argparse
from dotenv import load_dotenv

# Add parent directories to path to allow imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.processing.orchestrator import PipelineOrchestrator
from backend.config.pipeline_config import PipelineConfig

# Load environment variables
load_dotenv()

async def run_benchmark(pdf_path: str, output_dir: str):
    """
    Runs the pipeline and measures its performance.
    """
    print(f"--- Starting Benchmark for: {pdf_path} ---")
    
    # Start memory tracking
    tracemalloc.start()

    # --- Run Pipeline with Profiling ---
    orchestrator = PipelineOrchestrator()
    config = PipelineConfig(concurrency_limit=10)
    
    profiler = cProfile.Profile()
    profiler.enable()

    start_time = asyncio.get_event_loop().time()
    result = await orchestrator.process_document_async(pdf_path, config)
    end_time = asyncio.get_event_loop().time()
    
    profiler.disable()

    # Get memory usage
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # --- Print Report ---
    print("\n--- Performance Benchmark Report ---")
    print(f"Total Execution Time: {end_time - start_time:.2f}s")
    print(f"Peak Memory Usage: {peak / 10**6:.2f} MB")
    print(f"Total Pages Processed: {len(result['extraction_results'])}")
    print(f"Total Chunks Created: {result['chunking_stats']['total_chunks']}")
    
    print("\n--- cProfile Stats (Top 15 by cumulative time) ---")
    stats = pstats.Stats(profiler).sort_stats("cumulative")
    stats.print_stats(15)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a benchmark of the PDF extraction pipeline.")
    parser.add_argument("pdf_path", type=str, help="The path to the input PDF file.")
    parser.add_argument("--output_dir", type=str, default="scripts/output", help="The directory to save the output files.")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.pdf_path, args.output_dir))
