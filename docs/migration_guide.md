# Migration Guide

This guide explains how to migrate from the legacy PDF extraction pipeline to the refactored pipeline.

## Key Changes

The refactored pipeline introduces the following key changes:

- **Modular Architecture:** The monolithic `smart_extraction.py` file has been broken down into smaller, more manageable modules.
- **Parallel Processing:** The refactored pipeline can process multiple pages in parallel, which can significantly improve performance.
- **Centralized Configuration:** All configuration for the pipeline is now managed in a central location.

## Migration Steps

1.  **Update your code to call the new `PipelineOrchestrator` class instead of the `get_text_embed_improved_async` function.**
2.  **Update your configuration to use the new YAML-based configuration files.**
3.  **Run the `scripts/compare_pipelines.py` script to compare the output of the new pipeline with the legacy pipeline and ensure that the extraction quality is maintained.**
