# Configuration Guide

This guide provides a comprehensive overview of how to configure the Intelligent Document Extraction Pipeline. The configuration is split into three main pillars: high-level pipeline behavior, LLM model definitions, and feature flags.

## 1. Environment Variables (`.env`)

First, ensure you have a `.env` file in the project root. You can create one by copying the `.env.example` file. This file is used for storing secrets.

```sh
cp .env.example .env
```

The primary variable you need to set is your API key:

```dotenv
# .env
LLM_API_KEY="YOUR_API_KEY_HERE"
```

## 2. Main Pipeline Configuration (`pipeline_config.py`)

The main configuration for the pipeline's behavior is defined in the `PipelineConfig` class located at `backend/config/pipeline_config.py`. This class uses Pydantic for type-safe validation and provides default values for key operational parameters.

You can adjust these settings when you instantiate the `PipelineOrchestrator` in a script like `scripts/run_pipeline.py`.

### Key Configuration Options

Here are the primary attributes of the `PipelineConfig` class:

```python
class PipelineConfig(BaseModel):
    """
    Defines the high-level configuration for the extraction pipeline.
    """
    # The maximum number of pages to process concurrently.
    # Increasing this can improve speed but will use more memory and API calls.
    concurrency_limit: int = 10

    # The maximum number of LLM API calls to make per minute.
    # This is crucial for avoiding rate limit errors from the provider.
    rate_limit_per_minute: int = 100

    # The maximum number of times to retry a failed LLM call.
    retry_max_attempts: int = 3

    # The initial delay (in seconds) for the first retry.
    # Subsequent retries use exponential backoff.
    retry_initial_delay: float = 1.0

    # Enables the self-correction mechanism where the pipeline re-analyzes
    # an extraction result and can trigger a more specialized strategy if needed.
    iterative_refinement_enabled: bool = True

    # The maximum number of refinement loops to prevent infinite cycles.
    max_refinement_cycles: int = 2
```

### Example Usage (`scripts/run_pipeline.py`)

```python
from backend.processing.orchestrator import PipelineOrchestrator
from backend.config.pipeline_config import PipelineConfig

# ...

async def main(pdf_path: str, output_dir: str):
    orchestrator = PipelineOrchestrator(api_key="...")
    async with orchestrator.client:
        # Customize the pipeline configuration here
        config = PipelineConfig(
            concurrency_limit=5,
            iterative_refinement_enabled=False
        )

        result = await orchestrator.process_document_async(pdf_path, config)
        # ...
```

## 3. LLM Configuration (`llm_config.yaml`)

The configuration for all Large Language Models is externalized to `backend/config/llm_config.yaml`. This file is loaded into the `LLMConfig` Pydantic model, which provides a structured and validated way to manage models.

This YAML file defines:
- The models available for different tasks (routing, extraction, summarization).
- The API provider, token limits, and other metadata for each model.
- The fallback chains to use if a primary model fails.

### Example `llm_config.yaml`

```yaml
# backend/config/llm_config.yaml
default_models:
  router: "gemini-2.5-pro"
  extraction: "gemini-2.5-pro"
  summarizer: "gemini-2.5-pro"

models:
  gemini-2.5-pro:
    provider: "Google"
    token_limit: 32000
    is_vision_capable: true
    # Fallback model if gemini-2.5-pro fails
    fallback: "gpt-4.1"

  gpt-4.1:
    provider: "OpenAi"
    token_limit: 128000
    is_vision_capable: true
    # No fallback for this model
    fallback: null

  # Example of a non-vision model
  claude-opus-4:
    provider: "Anthropic"
    token_limit: 200000
    is_vision_capable: false
    fallback: null
```

## 4. Feature Flags (`feature_flags.yaml`)

Feature flags are used to enable or disable specific, non-essential features of the pipeline without changing the code. They are defined in `backend/config/feature_flags.yaml` and loaded via the `FeatureFlags` utility.

This allows for safe rollouts of experimental features.

### Example `feature_flags.yaml`

```yaml
# backend/config/feature_flags.yaml
# Use this file to toggle experimental or optional features.

# Enables a more detailed analysis in the refinement step.
enhanced_refinement_analysis:
  enabled: true
  description: "If enabled, the refinement analyzer uses a more detailed prompt to check for missed content."

# An example of a disabled feature
experimental_table_parser:
  enabled: false
  description: "If enabled, uses a new experimental library for table parsing instead of the default LLM-based one."
```