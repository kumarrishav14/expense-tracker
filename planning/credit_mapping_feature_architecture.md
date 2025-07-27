# Feature Architecture: Credit Mapping

**Author:** AI Architect
**Date:** July 24, 2025
**Version:** 1.0

## 1. Overview

This document provides the complete architecture for the **Credit Mapping** feature. The primary goal of this feature is to allow users to manually link credit card payments from their bank accounts to the corresponding credit card statements, thus preventing the double-counting of expenses. 

This architecture prioritizes simplicity, user control, and reliability over complex automation for its initial implementation. It is designed to be a robust foundation for potential future enhancements.

## 2. Core Concept: User-Driven Reconciliation

The core of this feature is a **manual reconciliation workflow** presented to the user within the application's UI. Instead of a complex backend engine trying to automatically find matches, the system will guide the user to make the connections themselves. This approach is simpler to build and more robust, as it leverages the user's own knowledge.

The workflow is centered around the lifecycle of a `card_statement`, which can be in one of three states: `UNPAID`, `PARTIALLY_PAID`, or `PAID`.

## 3. Database Schema Requirements

This feature requires the new `accounts`, `card_statements`, and `transfers` tables, as well as modifications to the `transactions` table.

*Reference: [Database Schema Architecture](db_model/schema_architecture.md)*

**Key Schema Addition:**

-   **`card_statements` table - Add `status` column:**
    -   `status` (String, NOT NULL, Default: `'UNPAID'`): Tracks the payment status of the statement. The possible values and their lifecycle are central to this feature:
        -   `UNPAID`: The initial state. No payments are linked.
        -   `PARTIALLY_PAID`: One or more payments are linked, but their sum is less than the statement's `total_due`.
        -   `PAID`: The sum of linked payments is greater than or equal to the `total_due`.

## 4. The Credit Mapping Workflow

### Step 1: System Becomes "Debt-Aware"
-   When a user uploads a credit card statement, a new record is created in the `card_statements` table with its `status` set to `'UNPAID'`.
-   The system now knows a specific bill is pending payment.

### Step 2: The Reconciliation UI is Triggered
-   The Credit Mapping UI is presented to the user whenever the system detects that there are statements in the `'UNPAID'` or `'PARTIALLY_PAID'` state. This check is performed after any statement (bank or credit card) is uploaded.

### Step 3: The User Creates the Link
-   The UI will present two lists:
    1.  **Potential Payments:** A list of unlinked, outgoing transactions from all bank accounts.
    2.  **Unpaid Bills:** A list of all `card_statements` with a status of `'UNPAID'` or `'PARTIALLY_PAID'`. The UI will clearly display the remaining balance for partially paid bills.
-   The user selects one item from each list and clicks a **"Link Payment"** button.

### Step 4: The System Executes the Link
-   Upon user confirmation, the system performs the following actions in a single, atomic database transaction:
    1.  Creates a new record in the `transfers` table.
    2.  Updates the selected bank transaction, setting `is_transfer = True`.
    3.  Recalculates the total amount paid towards the selected `card_statement`.
    4.  Updates the `card_statement`'s `status` to either `'PARTIALLY_PAID'` or `'PAID'` based on the new total.

## 5. High-Level Data and UI Flow

```mermaid
graph TD
    A[Upload Bank Statement] --> B{Check for Unpaid/Partially Paid Bills};
    B -- Yes --> C{Display Credit Mapping UI};
    B -- No --> D[Finish / Go to Dashboard];

    subgraph Credit Mapping UI
        C --> E[List of Potential Payments];
        C --> F["List of Unpaid Bills (with remaining balance)"];
    end

    E -- User Selects --> G((Link));
    F -- User Selects --> G;

    G -- 'Click Link Payment' --> H{System Executes Link};
    
    subgraph "System Logic (Single DB Transaction)"
        H --> I[Create 'transfers' record];
        H --> J[Update bank transaction 'is_transfer'];
        H --> K[Recalculate total paid for statement];
        H --> L[Update statement 'status'];
    end

    L --> B; 
    %% Re-check state and either exit or show remaining unpaid bills
```

## 6. Component Interaction Sequence

This sequence diagram illustrates the order of operations between the frontend, the main application logic, and the database layer when a user links a payment.

```mermaid
sequenceDiagram
    participant User
    participant UI as Frontend
    participant App as Application Logic
    participant DB as DB Interface

    User->>+UI: 1. Clicks "Link Payment" button

    UI->>+App: 2. handle_link_payment(payment_id, statement_id)

    App->>+DB: 3. begin_transaction()
    Note over App,DB: Start atomic operation

    App->>+DB: 4. link_transfer(payment_id, statement_id)
    DB-->>-App: 5. Returns success/failure

    App->>+DB: 6. flag_transaction_as_transfer(payment_id, ...)
    DB-->>-App: 7. Returns success/failure

    App->>+DB: 8. get_total_paid_for_statement(statement_id)
    DB-->>-App: 9. Returns total_paid

    App->>App: 10. Compare total_paid to statement.total_due
    App->>+DB: 11. update_statement_status(statement_id, new_status)
    DB-->>-App: 12. Returns success/failure

    App->>+DB: 13. commit_transaction()
    Note over App,DB: End atomic operation

    App-->>-UI: 14. Returns result (Success/Error)
    UI-->>-User: 15. Show confirmation message and refresh UI
```

This architecture provides a simple, robust, and user-centric solution for the Credit Mapping feature. It delivers immediate value while creating a solid foundation for future automation.
