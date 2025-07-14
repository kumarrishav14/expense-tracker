# Test Plan: Ollama Basic APIs

**Author:** Gemini Tester
**Date:** July 10, 2025

## 1. Objective

This test plan outlines the strategy for testing the basic, non-AI functionality of the `OllamaClient`. The goal is to ensure that server interaction APIs—such as connection testing, model listing, and info retrieval—are robust and handle both success and error scenarios correctly.

These tests will be pure unit tests, mocking external HTTP requests to ensure they are fast, repeatable, and do not require a running Ollama server.

## 2. Scope

### In Scope
- `OllamaClient.test_connection()`: Verifies server accessibility checks.
- `OllamaClient.list_models()`: Verifies fetching of available models.
- `OllamaClient.check_model_exists()`: Verifies logic for checking if a model is available.
- `OllamaClient.get_server_info()`: Verifies aggregation of server status and information.
- Exception Handling: Ensure custom exceptions (`OllamaConnectionError`, `OllamaAPIError`, etc.) are raised appropriately.

### Out of Scope
- `OllamaClient.generate_completion()`: AI-related functionality.
- `OllamaClient.categorize_transaction()`: AI-related functionality.
- `OllamaFactory` and `OllamaConfigManager` direct testing (they are tested implicitly via the client).
- Integration tests requiring a live Ollama server.

## 3. Test Strategy

- **Framework**: `pytest`
- **Mocking**: `pytest-mock` will be used to patch the `requests` library.
- **Fixtures**: `pytest` fixtures will be used to provide `OllamaConfig` and `OllamaClient` instances to test functions.
- **Assertions**: Tests will assert on return values and raised exceptions.

## 4. Test Cases

### `test_connection()`
- **Test 1**: Mock a successful API response; verify it returns `True`.
- **Test 2**: Mock a connection error; verify it returns `False`.
- **Test 3**: Mock a timeout; verify it returns `False`.
- **Test 4**: Mock a non-JSON or empty response; verify it returns `False`.

### `list_models()`
- **Test 1**: Mock a successful API response with models; verify it returns a list of model names.
- **Test 2**: Mock a successful response with no models; verify it returns an empty list.
- **Test 3**: Mock a connection error; verify `OllamaAPIError` is raised.

### `check_model_exists()`
- **Test 1**: Mock `list_models` to return a list of models; verify `True` is returned for an existing model.
- **Test 2**: Mock `list_models` to return a list of models; verify `False` is returned for a non-existent model.
- **Test 3**: Mock `list_models` to fail; verify `False` is returned.

### `get_server_info()`
- **Test 1**: Mock successful API calls; verify a complete dictionary with `is_connected: True` is returned.
- **Test 2**: Mock a failed API call; verify a dictionary with `is_connected: False` and an error message is returned.
