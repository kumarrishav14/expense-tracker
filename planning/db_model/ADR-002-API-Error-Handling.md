# ADR-002: API Error Handling and Return Types

**Date:** July 28, 2025
**Status:** Adopted

## Context

The application's API, particularly the `db_interface`, must provide a predictable and robust way for callers to handle both successful and failed operations. Previous architectural versions were inconsistent, returning a mix of `bool`, raw objects, and structured results, which created confusion and required callers to implement complex, branching logic to interpret the result of a method call.

We needed to decide on a single, universal philosophy for API return types.

## Decision

We will implement a **Structured, Two-Layer Error Handling Strategy**.

1.  **Internal Layer (`db_manager`): Raises Exceptions.**
    *   The `db_manager`, which performs raw database operations, will **not** handle errors. It will allow standard, specific SQLAlchemy exceptions (e.g., `IntegrityError`, `DataError`) to be raised and propagate upwards. This is a standard and robust Pythonic pattern.

2.  **Public API Layer (`db_interface`): Translates Exceptions to Structured Results.**
    *   The `db_interface` will serve as a translation layer. All of its data-modifying methods will be wrapped in a `try...except` block.
    *   On success, it will return a structured `OperationResult` or `BatchOperationResult` object with `success=True`.
    *   On failure, it will **catch** the specific exception from the `db_manager` and **translate** it into a structured `OperationResult` or `BatchOperationResult` with `success=False` and rich error context (error message, category, whether it is retryable).

**Conclusion:** No method in the `db_interface` that can fail will return a raw object or a simple boolean. It will always return a structured result.

## Rationale

This pattern provides several key benefits:

-   **Predictability:** The caller of any `db_interface` method always receives the same object shape. The handling logic is always `if result.success: ... else: ...`, which is simple and unambiguous.
-   **Rich Context:** Failures are no longer a simple `False`. The result object provides the caller with everything they need to know: *what* went wrong (`error_message`), *why* it went wrong (`error_category`), and *what to do next* (`is_retryable`).
-   **Clean Separation of Concerns:** The `db_manager` is only concerned with database logic. The `db_interface` is only concerned with the application's API contract. This separation makes the system easier to understand, test, and maintain.
-   **No Silent Failures:** This pattern makes it impossible for an error to be accidentally ignored, as the `success` flag must always be checked.

## Consequences

-   **Implementation Discipline:** All new `db_interface` methods must adhere strictly to this `try...except...translate` pattern.
-   **No Leaky Exceptions:** Low-level database exceptions are an implementation detail. They should never leak past the `db_interface` boundary to the rest of the application.
-   **Caller Responsibility:** The application code that calls the `db_interface` is responsible for inspecting the `OperationResult` and taking the appropriate action (e.g., showing an error to the user, retrying the operation).
