# Frontend Micro-Architecture: Statement Input Tab

**Author:** AI Architect
**Date:** July 10, 2025

## 1. Component Overview

This document provides the detailed micro-architecture for the **Statement Input Tab**. This tab is the primary user entry point for uploading and processing new transaction files (PDFs, CSVs, etc.).

This design adheres to the principles outlined in the main `frontend_micro_architecture.md` document. It follows a streamlined, two-step user workflow: **Process & Review -> Save**.

## 2. Responsibilities

-   Provide a file uploader widget for supported file types.
-   Orchestrate the password-handling flow for encrypted PDFs behind the scenes.
-   Provide a single action button (e.g., "Process & Review") to trigger the entire backend data pipeline (parsing and processing).
-   Display a final, editable preview of the fully processed and categorized data. The user should not be shown raw, intermediate data.
-   Allow users to review and correct AI-assigned categories directly in the preview table.
-   Provide a mechanism to save the final, user-verified data to the database.
-   Show clear success, error, and progress messages to the user.

## 3. State Management (`st.session_state`)

-   `st.session_state.processed_df`: A pandas DataFrame holding the fully standardized and categorized data, ready for user review and editing. This is the primary data state for this tab.
-   `st.session_state.upload_error`: A string to hold any error message from the entire backend pipeline (parsing or processing), to be displayed with `st.error()`.

## 4. Component Logic and Sequence

This sequence details the streamlined **Process & Review -> Save** workflow. It combines parsing and processing into a single user action to provide a better user experience. The user is only shown the final, clean data.

```mermaid
sequenceDiagram
    actor User
    participant UI as Statement Input Tab
    participant Backend as Backend Handler
    participant Parser as Parser Backend
    participant Processor as DataProcessor
    participant DB as DB Interface

    User->>+UI: 1. Uploads file
    Note over UI: Displays "Process & Review" button.

    User->>+UI: 2. Clicks "Process & Review"
    UI->>+Backend: 3. Passes file stream (and password if needed)
    
    Note over Backend: Backend executes the full pipeline...
    Backend->>+Parser: 4. Parse file (PDF/CSV)
    Parser-->>-Backend: 5. Returns raw DataFrame
    
    Backend->>+Processor: 6. process_raw_data(raw_df)
    Processor-->>-Backend: 7. Returns processed_df (with AI categories)

    Backend-->>-UI: 8. Returns final, processed DataFrame

    UI->>+DB: 9. get_all_categories()
    DB-->>-UI: 10. Returns list of categories for dropdown
    Note over UI: Displays editable table (st.data_editor) with AI categories ready for review.
    
    User->>+UI: 11. Reviews and corrects categories
    User->>+UI: 12. Clicks "Confirm & Save"
    
    UI->>+DB: 13. save_transactions_table(final_df)
    DB-->>-UI: 14. Returns success/failure
    UI-->>-User: 15. Displays final success message
```

## 5. Error Handling

-   The UI **must** wrap the entire backend pipeline call (parsing and processing) in a single `try...except ValueError` block.
-   Any `ValueError` raised from either the `Parser` or the `DataProcessor` will be caught and its message will be stored in `st.session_state.upload_error` and displayed to the user using `st.error()`. This provides a single, clean point for error feedback.
