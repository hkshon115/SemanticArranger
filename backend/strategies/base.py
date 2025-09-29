from abc import ABC, abstractmethod
import time
from backend.config.pipeline_config import PipelineConfig
from backend.core.interfaces import PageData
from backend.llm_app.async_client import AsyncLLMClient
from backend.models.extraction import ExtractionPlan, ExtractionResult
from backend.utils.validators import parse_extraction_response


class IExtractionStrategy(ABC):
    """
    An interface for an extraction strategy. It defines the contract that all
    concrete strategy implementations must follow.
    """

    @abstractmethod
    async def execute_plan(
        self, plan: ExtractionPlan, page_data: PageData, config: PipelineConfig
    ) -> ExtractionResult:
        """
        Executes the extraction plan for a given page.

        Args:
            plan: The `ExtractionPlan` for the current step.
            page_data: The `PageData` object containing the page's content.
            config: The pipeline configuration.

        Returns:
            An `ExtractionResult` object with the outcome of the extraction.
        """
        pass


class BaseStrategy(IExtractionStrategy, ABC):
    """
    An abstract base class for all extraction strategies.

    This class contains the shared logic for executing an extraction plan,
    including calling the LLM and handling the response. Concrete strategies
    must implement the `_create_content` method to provide the specific
    prompt and content for their use case.
    """

    def __init__(self, client: AsyncLLMClient):
        """
        Initializes the BaseStrategy.

        Args:
            client: An instance of `AsyncLLMClient` for making API calls.
        """
        self.client = client

    @abstractmethod
    def _create_content(
        self, page_data: PageData, plan: ExtractionPlan, config: PipelineConfig
    ) -> list:
        """
        Prepares the specific content payload for the LLM API call.
        This method must be implemented by each concrete strategy.
        """
        pass

    async def execute_plan(
        self, plan: ExtractionPlan, page_data: PageData, config: PipelineConfig
    ) -> ExtractionResult:
        """
        Executes the extraction plan by calling the LLM and handling the response.
        This method is shared across all strategies.
        """
        start_time = time.time()

        content = self._create_content(page_data, plan, config)

        response = await self.client.chat(
            model=config.extraction_primary_model,
            content=content,
            system="You are a precise document analyzer. Return only valid JSON.",
            max_tokens=plan.max_tokens,
            temperature=0.1,
        )

        elapsed = time.time() - start_time

        if response.get("error"):
            return ExtractionResult(
                step=plan.step,
                strategy=plan.strategy.value,
                success=False,
                error=response["error"],
                tokens_used=0,
                time_elapsed=elapsed,
            )

        parsed_content = parse_extraction_response(response.get("content", ""))

        if not parsed_content:
            return ExtractionResult(
                step=plan.step,
                strategy=plan.strategy.value,
                success=False,
                error="Failed to parse JSON response from the model.",
                tokens_used=response.get("usage", {}).get("total_tokens", 0),
                time_elapsed=elapsed,
            )

        return ExtractionResult(
            step=plan.step,
            strategy=plan.strategy.value,
            success=True,
            content=parsed_content,
            tokens_used=response.get("usage", {}).get("total_tokens", 0),
            time_elapsed=elapsed,
        )