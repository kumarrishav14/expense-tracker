# ADR-001: Dual Session Management Pattern

**Date:** July 28, 2025
**Status:** Adopted

## Context

The application requires a database interaction model that can support two distinct use cases:

1.  **Simple, self-contained operations:** A user updates a single account name. This operation should be atomic and commit on its own without requiring the caller to manage a transaction.
2.  **Complex, multi-step operations:** A user saves a table of transactions which may also require creating new category hierarchies. This entire sequence of operations must be atomic—either everything succeeds, or everything is rolled back.

A naive implementation could lead to session contamination (as seen in previous versions) or force all callers to manage transactions, which adds unnecessary complexity to simple operations.

## Decision

We will implement a **Dual Session Management Pattern** using an optional `session` parameter in the persistence methods of the `db_interface` and `db_manager` layers.

1.  **Method Signature:** All methods that perform database writes will have the signature `method(self, ..., session: Optional[Session] = None)`.

2.  **Behavior:**
    *   If `session` is **`None`** (the default), the method is responsible for its own transaction. It will acquire a new session, perform its operation, and commit upon successful completion. This is the "auto-commit" mode for simple operations.
    *   If a `session` object is **provided**, the method will use that existing session to perform its operation. It will **not** commit the transaction, as it assumes the transaction is being managed by an external caller (typically a `transaction_scope` context manager).

## Rationale

This pattern provides the maximum flexibility and safety with the cleanest API:

-   **Simplicity for Simple Cases:** Callers performing a single operation do not need to know what a transaction is. They can simply call `db_interface.update_account(...)` and it works.
-   **Power for Complex Cases:** Callers performing multiple related operations can guarantee atomicity by creating a single transaction scope and passing the session to each operation.
-   **Prevents Session Contamination:** By always using a new, clean session for auto-committed operations and a dedicated session for complex transactions, we eliminate the risk of stateful session objects being reused after a rollback.

## Consequences

-   **Implementation Discipline:** All developers writing persistence methods **must** adhere to this pattern.
-   **Caller Awareness:** Developers using the `db_interface` for complex, multi-step writes must understand that they need to use the `transaction_scope` to ensure atomicity.
-   **Testing:** Tests must be written to account for both modes of operation (with and without a provided session).
