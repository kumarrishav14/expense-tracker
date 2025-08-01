# Frontend Micro-Architecture: Statement Input Tab

**Author:** AI Architect
**Date:** July 31, 2025
**Status:** Finalized
**Version:** 2.0

## 1. Component Overview

This document provides the detailed micro-architecture for the **Statement Input Tab**. This tab is the primary entry point for user data, handling the upload and initial processing of financial statements.

This architecture is based on a **user-driven workflow**, where the user is in full control of associating statements with accounts. This approach prioritizes reliability and simplicity over complex automation.

## 2. Core Concept: The Upload State Machine

The tab's UI and logic will operate as a simple state machine, driven by `st.session_state`. The tab can be in one of the following primary states:

1.  **`AWAITING_UPLOAD`**: The initial state. The UI displays the file uploader widget.
2.  **`AWAITING_PASSWORD`**: An intermediary state triggered if the user uploads a password-protected PDF.
3.  **`AWAITING_ACCOUNT_SELECTION`**: The state triggered after a file is successfully uploaded (and decrypted, if necessary). The user is prompted to select an account.
4.  **`READY_FOR_PROCESSING`**: The state where a file has been uploaded and associated with a user-selected account, and is ready for the main data processing pipeline.

## 3. The User-Driven Workflow

This is the central workflow of the tab. It removes all automatic detection in favor of explicit user control.

```mermaid
graph TD
    A[Start: Awaiting Upload] -->|User uploads file| B{Check File Type};
    B --> B_PDF{File is PDF};
    B --> B_CSV[File is CSV];

    B_PDF --> P1{Is PDF Encrypted?};
    P1 -- Yes --> P2[Await Password];
    P1 -- No --> C(Awaiting Account Selection);
    P2 --> C;
    B_CSV --> C;

    C --> D{Display Account Dropdown};
    D -->|User selects Existing Account| F(Ready for Processing);
    D -->|User selects "--- Add New Account ---"| E{Show 'Add Account' Form In-Place};
    E -->|User saves new account| F;

    F -->|User clicks "Process"| G[Call Parser & Processor];
    G --> H(Processing Complete);
```

## 4. UI and Component Design

### 4.1. State 1: `AWAITING_UPLOAD`
-   **UI:** A standard `st.file_uploader` is displayed.
-   **Logic:** When a file is uploaded, the component checks if it is a PDF. If so, it checks for encryption and may transition to `AWAITING_PASSWORD`. Otherwise, it transitions directly to `AWAITING_ACCOUNT_SELECTION`.

### 4.2. State 2: `AWAITING_PASSWORD`
-   **UI:** The file uploader is hidden. The UI displays a simple `st.text_input` for the password and an "Unlock" button.
-   **Logic:** On success, it stores the decrypted file object in session state and transitions to `AWAITING_ACCOUNT_SELECTION`. On failure, it shows an error message.

### 4.3. State 3: `AWAITING_ACCOUNT_SELECTION`
-   **UI:** The file uploader and password input are hidden. The UI displays:
    -   A message: "Please select the account for this statement."
    -   An `st.selectbox` populated with all active accounts from the database, plus a special `"--- Add New Account ---"` option.
    -   If "Add New Account" is selected, an `st.expander` appears with a form to create a new account.
-   **Logic:** Handles the selection of an existing account or the creation of a new one. Once an account is determined, the state transitions to `READY_FOR_PROCESSING`.

### 4.4. State 4: `READY_FOR_PROCESSING`
-   **UI:** All previous inputs are hidden. The UI displays:
    -   A confirmation message: "File ready for account '[Selected Account Name]'."
    -   A "Process Statement" button.
-   **Logic:** When the user clicks "Process Statement," the file data and the selected `account_id` are sent to the main data processing pipeline.

## 5. State Management

-   The entire workflow is orchestrated by a single session state variable, e.g., `st.session_state.upload_flow_state`.
-   Other session state variables will be used to hold the uploaded file data (`st.session_state.uploaded_file_data`) and the determined `account_id` across reruns.

This architecture ensures that no transaction is ever processed without being explicitly linked to a user-selected account, providing a robust and user-friendly data ingestion pipeline.
