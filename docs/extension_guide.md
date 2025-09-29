# Extension Guide

This guide explains how to extend the Intelligent Document Extraction Pipeline with new functionality. The system's modular, strategy-based architecture makes it straightforward to add new capabilities.

## 1. Adding a New Extraction Strategy

The most common extension is to add a new extraction strategy. This allows you to define a custom process for handling specific types of content or pages.

### Step 1: Define the Strategy Class

1.  Create a new Python file in the `backend/strategies/` directory (e.g., `my_new_strategy.py`).
2.  In this file, create a class that inherits from the `BaseExtractionStrategy` abstract base class.
3.  Implement the `execute_plan_async` method. This method contains the core logic for your strategy. It receives the page content and the extraction plan and should return an `ExtractionResult`.

**Example: `my_new_strategy.py`**

```python
# backend/strategies/my_new_strategy.py
from backend.strategies.base import BaseExtractionStrategy
from backend.models.extraction import ExtractionPlan, ExtractionResult
from backend.llm_app.async_client import AsyncHChatClient
from backend.config.llm_config import LLMConfig

class MyNewStrategy(BaseExtractionStrategy):
    """
    A new strategy for extracting QR codes and their associated text.
    """
    def __init__(self, client: AsyncHChatClient, llm_config: LLMConfig):
        super().__init__(client, llm_config)
        self.strategy_name = "my_new_strategy"

    async def execute_plan_async(
        self,
        page_content: Dict[str, Any],
        plan: ExtractionPlan,
        is_fallback: bool = False,
    ) -> ExtractionResult:
        
        # 1. Define a custom prompt for the new task
        prompt = self.get_custom_prompt(plan)

        # 2. Make the LLM call
        llm_response = await self.client.get_completion_with_fallbacks(
            messages=[{"role": "user", "content": [{"type": "image_url", ...}, {"type": "text", "text": prompt}]}],
            model=self.llm_config.get_default_model("extraction"),
            # ... other parameters
        )

        # 3. Process the response and structure it
        # ... (your logic here)

        # 4. Return a standardized ExtractionResult
        return ExtractionResult(
            step=plan.step,
            strategy=self.strategy_name,
            success=True,
            content={"qr_code_data": "...", "associated_text": "..."},
            # ... other fields
        )

    def get_custom_prompt(self, plan: ExtractionPlan) -> str:
        # Your prompt engineering logic here
        return "Find and extract data from QR codes on this page."
```

### Step 2: Update the `ExtractionStrategy` Enum

Add your new strategy's name to the `ExtractionStrategy` enum in `backend/models/extraction.py`. This makes the system aware of your new strategy.

```python
# backend/models/extraction.py
class ExtractionStrategy(str, Enum):
    # ... existing strategies
    MY_NEW_STRATEGY = "my_new_strategy"
```

### Step 3: Register the Strategy in the Factory

Finally, register your new strategy in the `StrategyFactory` located at `backend/strategies/factory.py`. This allows the `AsyncExtractor` to instantiate your strategy when it's requested in an extraction plan.

```python
# backend/strategies/factory.py
from backend.strategies.my_new_strategy import MyNewStrategy
# ... other imports

class StrategyFactory:
    def __init__(self, client: AsyncHChatClient, llm_config: LLMConfig):
        self._strategies = {
            # ... existing strategies
            ExtractionStrategy.MY_NEW_STRATEGY: MyNewStrategy(client, llm_config),
        }
```

Your new strategy is now fully integrated. The `AsyncRouter` can start recommending `"my_new_strategy"` in its extraction plans, and the `AsyncExtractor` will automatically use it.

## 2. Adding Support for a New Document Format

Adding support for a new document format (e.g., DOCX, HTML) requires creating a new document parser that can adapt the source file into the pipeline's internal `PageData` representation.

1.  **Create a New Parser:**
    - Create a new class in `backend/utils/document_parser.py` (or a new file).
    - This class should have a method that takes a file path and returns a list of `PageData` objects. Each `PageData` object must contain the page number, dimensions, and a PIL Image object of the page's visual representation. For text-based formats like HTML, you may need to use a library like `selenium` or `playwright` to render the content to an image.

2.  **Update the `DocumentParser`:**
    - Modify the `DocumentParser` class to detect the new file type (based on its extension or MIME type).
    - Based on the file type, delegate the parsing task to your new parser.

3.  **Consider the `AsyncRouter`:**
    - The `AsyncRouter` relies on a visual representation of each page. Ensure your new parser can provide a high-quality image for the router to analyze. For non-visual formats, this rendering step is critical.

## 3. Adding a New LLM Provider

The system is designed to be provider-agnostic. To add a new LLM provider (e.g., a local LLM server):

1.  **Create a Provider Class:**
    - Go to `backend/llm_app/providers/` and create a new file (e.g., `my_provider.py`).
    - Create a class that inherits from `BaseLLMProvider`.
    - Implement the `get_completion_async` method. This method will contain the logic for making API calls to your new provider, including handling authentication, request formatting, and response parsing.

2.  **Update the `AsyncHChatClient`:**
    - Modify the `AsyncHChatClient` in `backend/llm_app/async_client.py`.
    - In the `__init__` method, instantiate your new provider class.
    - In the `_get_provider` method, add logic to select your new provider based on the `provider` field in the `llm_config.yaml`.

3.  **Update `llm_config.yaml`:**
    - You can now add new models to your `llm_config.yaml` that use your new provider name.

    ```yaml
    # backend/config/llm_config.yaml
    models:
      my-local-llm:
        provider: "my_new_provider" # This should match your key in the client
        token_limit: 8000
        is_vision_capable: false
        fallback: null
    ```