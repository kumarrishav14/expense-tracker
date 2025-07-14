# Test Plan: Re-enabling AI Categorization

**Author:** Gemini Tester
**Date:** July 10, 2025

## 1. Objective

This document outlines the plan to re-enable tests for the AI-powered transaction categorization in the `DataProcessor`. With the `ai.ollama` backend now available, these tests will be activated to verify the integration and functionality of the categorization feature.

## 2. Test Strategy

To ensure tests are deterministic and independent of the live AI model's responses, the core of this strategy is to **mock the AI client's behavior**.

- **Framework**: `pytest`
- **Mocking**: `pytest-mock` will be used to patch the `categorize_expense` function that the `DataProcessor` calls. This mock will return predictable categories based on keywords in the transaction description, allowing for reliable assertions.

## 3. Execution Plan

1.  **Activate AI Test Suite**: Rename `tests/processors/data_processor/test_add_ai_categories_full.py.disabled` to `test_add_ai_categories_full.py`.

2.  **Create Mocking Fixture**: Add a new `pytest` fixture to `tests/processors/data_processor/conftest.py`. This fixture, named `mock_ai_categorization`, will patch the AI call and simulate its behavior.

3.  **Update AI Categorization Test**: Modify a test case within the newly activated test file (e.g., `test_keyword_matching_food_dining`) to use the `mock_ai_categorization` fixture and assert the expected outcome.

4.  **Update Integration Test**: Uncomment a disabled AI-related assertion in `tests/processors/data_processor/test_integration.py` to ensure the categorization works correctly within the end-to-end processing pipeline, also using the mock.

5.  **Run Tests**: Execute the modified test files to verify that the AI categorization logic is being called correctly and that the tests pass.

## 4. Scope

- **In Scope**: Enabling a foundational set of tests for basic categorization scenarios (e.g., Food, Shopping, Default).
- **Out of Scope**: Exhaustive testing of all possible categories or the accuracy of the live AI model itself. The focus is on verifying the `DataProcessor` correctly integrates with the AI module.
