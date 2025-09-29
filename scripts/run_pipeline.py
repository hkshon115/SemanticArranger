import asyncio
import os
import argparse
import json
from dotenv import load_dotenv

# Add parent directory to path to allow imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.processing.orchestrator import PipelineOrchestrator
from backend.config.pipeline_config import PipelineConfig

# Load environment variables
load_dotenv()

async def main(pdf_path: str, output_dir: str):
    """
    Main entry point for running the extraction pipeline.
    """
    print(f"--- Starting Pipeline for: {pdf_path} ---")
    
    orchestrator = PipelineOrchestrator()
    async with orchestrator.client:
        config = PipelineConfig(
            concurrency_limit=10,
            iterative_refinement_enabled=True
        )

        # Run the pipeline
        result = await orchestrator.process_document_async(
            pdf_path, config
        )

        # Save the results
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "extraction_results.json"), "w", encoding="utf-8") as f:
            json.dump(result["extraction_results"], f, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "executive_summary.json"), "w", encoding="utf-8") as f:
            json.dump(result["executive_summary"], f, indent=2, ensure_ascii=False)
        with open(os.path.join(output_dir, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(result["chunks"], f, indent=2, ensure_ascii=False)

        print(f"\n--- Pipeline Finished ---")
        print(f"Results saved to: {output_dir}")
        print(f"  - Pages Processed: {len(result['extraction_results'])}")
        print(f"  - Chunks Created: {result['chunking_stats']['total_chunks']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the PDF extraction pipeline.")
    parser.add_argument("pdf_path", type=str, help="The path to the input PDF file.")
    parser.add_argument("--output_dir", type=str, default="scripts/output", help="The directory to save the output files.")
    args = parser.parse_args()

    asyncio.run(main(args.pdf_path, args.output_dir))
