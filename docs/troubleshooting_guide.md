# Troubleshooting Guide

This guide provides solutions to common problems you may encounter when using the Intelligent Document Extraction Pipeline.

## 1. Configuration & Setup Errors

---

### Problem: `401 Unauthorized` or API Key Errors

- **Symptom:** The script fails immediately with an authentication error, often containing `401 Unauthorized`.
- **Cause:** The `HCHAT_API_KEY` is either missing, incorrect, or not loaded properly.
- **Solution:**
    1.  Ensure you have a `.env` file in the project's root directory.
    2.  Verify that the `HCHAT_API_KEY` in your `.env` file is correct and has no extra spaces or characters.
    3.  Make sure you are running the script from the root of the project so that `load_dotenv()` can find the `.env` file.

---

### Problem: `FileNotFoundError`

- **Symptom:** The script fails with an error indicating that the input PDF file was not found.
- **Cause:** The path provided for the PDF file is incorrect.
- **Solution:**
    1.  Double-check that the path to the PDF file is correct.
    2.  Use an absolute path or ensure the relative path is correct based on your current working directory.

---

### Problem: `pymupdf.FileDataError` or Invalid PDF

- **Symptom:** The pipeline fails with an error related to `pymupdf`, indicating the file is corrupted or not a valid PDF.
- **Cause:** The target file is not a well-formed PDF.
- **Solution:**
    1.  Try opening the file in a standard PDF viewer (like Adobe Acrobat or your web browser) to confirm it is a valid, uncorrupted PDF.
    2.  If the file is password-protected, it will also fail. Ensure the PDF is decrypted.

## 2. Pydantic `ValidationError` During Runtime

This is a common issue when the JSON output from an LLM does not match the expected Pydantic model schema. The error message will typically point to the exact field that failed validation.

---

### Problem: `ValidationError` in `RouterAnalysis`

- **Symptom:** The logs show a `Router exception` followed by a Pydantic `ValidationError`, often complaining about a type mismatch (e.g., `Input should be a valid integer, unable to parse string`).
- **Cause:** The `AsyncRouter`'s LLM call produced a JSON structure that does not match the `RouterAnalysis` model in `backend/models/extraction.py`. This usually happens if the LLM provides a descriptive string (e.g., `"A single large table"`) when the model expects an integer (e.g., `1`).
- **Solution:**
    1.  **Inspect the failed output:** The primary cause is a mismatch between the prompt and the model. The `ROUTER_ANALYSIS_PROMPT` in `backend/config/prompt_templates.py` may be too ambiguous for the model you are using.
    2.  **Make the Pydantic Model More Flexible (Recommended):** The most robust solution is often to relax the Pydantic model. For example, if a field like `visual_elements` is causing issues, changing its type from `int` to `Dict[str, Any]` in the `RouterAnalysis` model can make the system more resilient to variations in LLM output.
    3.  **Refine the Prompt:** Alternatively, you can make the prompt more restrictive. Add explicit instructions to the `ROUTER_ANALYSIS_PROMPT` to provide *only* an integer count for the problematic field.

---

### Problem: `ValidationError` in `ExtractionResult`

- **Symptom:** The error occurs after the routing step, during the execution of an extraction strategy.
- **Cause:** The prompt for a specific extraction strategy (e.g., `COMPREHENSIVE` or `TABLE_FOCUS`) is producing JSON that doesn't match the structure expected by the strategy's processing logic.
- **Solution:**
    1.  Identify which strategy was running when the error occurred.
    2.  Examine the corresponding prompt in `backend/config/prompt_templates.py`.
    3.  Compare the JSON structure in the prompt with the logic that parses the LLM's response within the strategy file (in `backend/strategies/`). Adjust the prompt or the parsing logic to align them.

## 3. Performance Issues

---

### Problem: The pipeline is running slowly.

- **Cause:** The concurrency limit may be too low for your machine, or you are processing a very large document without caching.
- **Solution:**
    1.  **Increase Concurrency:** In your script (e.g., `run_pipeline.py`), increase the `concurrency_limit` in the `PipelineConfig` instantiation. A value between `10` and `20` is often a good starting point, but this is highly dependent on your machine's resources and your API provider's rate limits.
        ```python
        config = PipelineConfig(concurrency_limit=15)
        ```
    2.  **Check Rate Limiting:** Ensure the `rate_limit_per_minute` is set appropriately for your API key. If it's too low, the pipeline will be artificially slowed down.
    3.  **Enable Caching (if applicable):** If a caching mechanism is implemented, enable it in the configuration to speed up repeated runs on the same document.

## 4. Debugging Tips

- **Inspect the Output Files:** The JSON files saved in the `output` directory (`extraction_results.json`, `chunks.json`, etc.) are your best source of truth. Examine them to see what the pipeline successfully extracted before it failed or to understand why the output isn't what you expected.
- **Add Logging:** Use the `logging` module to add print statements or log messages in different parts of the pipeline (e.g., in the `AsyncRouter` or a specific strategy) to trace the data flow and inspect intermediate values.