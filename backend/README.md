# Backend Architecture

This directory contains the backend for the PDF extraction pipeline. It is designed as a modular, high-performance system for extracting structured data from documents using Large Language Models (LLMs).

## Core Architectural Principles

-   **Asynchronous Processing**: The entire pipeline is built on Python's `asyncio` to handle I/O-bound operations (like LLM API calls) concurrently, significantly improving throughput.
-   **Modularity & Separation of Concerns**: Each component has a single, well-defined responsibility. For example, the `core` modules handle the fundamental logic of extraction, while the `processing` modules orchestrate the high-level flow.
-   **Strategy Pattern**: The system uses a pluggable strategy pattern for data extraction. This allows for different extraction techniques (e.g., for text, tables, or visuals) to be developed and used interchangeably, making the system highly extensible.
-   **Resilience**: The pipeline is designed to be fault-tolerant, with built-in mechanisms for retries, model fallbacks, and graceful error handling.

## Directory Structure

-   `config/`: Centralized configuration for the pipeline. This includes LLM model definitions (`llm_config.yaml`), operational settings (`pipeline_config.py`), and all LLM prompts (`prompt_templates.py`).
-   `core/`: Contains the primary logic for the extraction process.
    -   `router.py`: The "brain" of the pipeline; analyzes a page and creates a strategic extraction plan.
    -   `extractor.py`: Executes the extraction plan using the appropriate strategies.
    -   `merger.py`: Consolidates the results from multiple extraction steps into a single, coherent output.
-   `llm_app/`: A provider-agnostic client for interacting with various LLM APIs (e.g., Claude, Gemini, Azure OpenAI). It handles API requests, responses, and errors.
-   `models/`: Defines the Pydantic data models that provide structure and type-safety for configuration and data transfer between components.
-   `processing/`: Contains the high-level components that orchestrate the end-to-end pipeline.
    -   `orchestrator.py`: The main entry point that wires all components together.
    -   `parallel_processor.py`: Manages the concurrent processing of document pages.
    -   `chunker.py`: Splits extracted text into smaller chunks for downstream use.
    -   `summarizer.py`: Generates an executive summary of the document.
-   `refinement/`: Implements the self-correction logic, where the pipeline can analyze its own output and trigger a second, more focused extraction to improve accuracy.
-   `resilience/`: Provides modules for error handling and fault tolerance, such as retries with exponential backoff, model fallback chains, and a circuit breaker pattern.
-   `strategies/`: Contains the individual extraction strategies. Each strategy is a self-contained plugin that implements a specific method for data extraction (e.g., `TableFocusedStrategy`, `VisualStrategy`).
-   `utils/`: Shared utility functions used across the application, such as document parsing, caching, and structured logging.
-   `tests/`: Unit and integration tests for the backend code.