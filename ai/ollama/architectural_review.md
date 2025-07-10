# Ollama Module - Architecture Review

**Author:** AI Architect
**Date:** July 10, 2025

## 1. Overall Assessment

This document provides an architectural review of the `ai.ollama` module.

The developer has implemented a well-structured and simple module that effectively encapsulates the logic for interacting with the Ollama service. The separation of concerns into `client`, `config`, and `factory` files is a strong design choice that enhances maintainability.

The implementation provides a solid foundation. The following recommendations are intended to further improve its robustness, portability, and ease of maintenance, aligning with best practices even for personal and open-source projects.

## 2. Key Strengths

- **Modularity**: The code is correctly divided into logical modules (client, configuration, factory), making it easy to understand and maintain.
- **Configuration Flexibility**: The `OllamaConfigManager` provides a solid approach, allowing configuration via a JSON file or environment variables. This is excellent for supporting different deployment environments.
- **Abstraction**: The `OllamaFactory` provides a clean, high-level abstraction for the rest of the application, simplifying client instantiation.
- **Resilience**: The fallback mechanism in `categorize_expense` is a crucial feature that ensures the application remains functional if the AI service fails.

## 3. Architectural Recommendations for Improvement

### 3.1. Replace `curl` with a Python HTTP Library

- **Critique**: The current implementation shells out to the `curl` command via `subprocess`. This creates a hard dependency on an external program, which harms portability and makes the application brittle. If `curl` is not in the system's PATH or has a different version, the application will fail. Error handling is also limited to parsing stdout/stderr.
- **Recommendation**: **Strongly recommend** replacing `subprocess` calls with a standard Python HTTP client library like `requests` or `httpx`. This dependency should be added to the `pyproject.toml` file and managed by `uv`.
- **Benefit**: This will make the application self-contained and portable across different environments without external dependencies. It will also enable more robust, idiomatic error handling (e.g., catching `ConnectionError`, `Timeout`) and simplify the code.

### 3.2. Refine Dependency Flow

- **Critique**: In `OllamaConfigManager.get_client_config`, a local import (`from .client import OllamaConfig`) is used. This often indicates a circular dependency or a suboptimal code structure. The configuration module should not depend on the client module.
- **Recommendation**: The `OllamaConfig` dataclass is a simple data container that logically belongs in the configuration module.
  1. Move the `OllamaConfig` dataclass from `ai/ollama/client.py` to `ai/ollama/config.py`.
  2. Update `client.py` to import `OllamaConfig` from `ai.ollama.config`.
- **Benefit**: This change establishes a clear, unidirectional dependency flow: `factory` -> `client` -> `config`, which is easier to reason about and maintain.

### 3.3. Externalize Prompts

- **Critique**: The prompt for transaction categorization is currently hardcoded inside the `categorize_transaction` method in `client.py`. This mixes application logic with prompt engineering, making the prompt difficult to inspect, version, or modify without changing the code.
- **Recommendation**: Move the prompt text into a separate template file within the existing `prompts/` directory (e.g., `prompts/expense_categorization.txt`). The application can load this file at runtime and format it with the required variables.
- **Benefit**: This decouples the prompt from the application code, allowing for easier iteration and tuning of the prompt without requiring code changes.

### 3.4. Improve Exception Handling

- **Critique**: The current error handling catches specific exceptions but then re-raises a generic `Exception` with a formatted string. This practice, known as "exception swallowing," loses the original exception's type and traceback, making it difficult for callers to handle different error scenarios programmatically.
- **Recommendation**: When replacing `curl`, allow the specific exceptions from the chosen HTTP library (e.g., `requests.exceptions.ConnectionError`) to propagate. Alternatively, define a small set of custom exceptions (e.g., `OllamaConnectionError`) that wrap the original exception, preserving the context.
- **Benefit**: This provides richer error information to the rest of the application, enabling more intelligent error handling (e.g., specific user messages for connection vs. server errors).

## 4. Conclusion

The developer has done a great job creating a functional and well-organized module.

By addressing the recommendations above—starting with the replacement of `curl`—the module will become significantly more robust, portable, and easier to maintain in the long run.
