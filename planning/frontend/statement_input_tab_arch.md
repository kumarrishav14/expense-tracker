# Frontend Micro-Architecture: Statement Input Tab

**Author:** AI Architect
**Date:** July 24, 2025
**Status:** Draft
**Version:** 1.0

## 1. Component Overview

This document provides the detailed micro-architecture for the **Statement Input Tab**. This tab is the primary entry point for user data, handling the upload and initial processing of financial statements.

This version introduces the **Smart Onboarding** workflow, a critical feature that intelligently handles account identification and creation during the file upload process. This workflow is designed to be seamless for the user while ensuring all incoming transactions are correctly associated with a user-defined account.

## 2. Core Concept: The Upload State Machine

The tab's UI and logic will operate as a simple state machine, driven by the `st.session_state`. The tab can be in one of the following primary states:

1.  **`AWAITING_UPLOAD`**: The initial state. The UI displays the file uploader widget.
2.  **`AWAITING_PASSWORD`**: An intermediary state triggered if the user uploads a password-protected PDF.
3.  **`AWAITING_ACCOUNT_SELECTION`**: The state triggered when a user uploads a file that the system does not recognize.
4.  **`AWAITING_PROCESSING`**: The state where a file has been successfully uploaded and associated with an account, and is ready for the main data processing pipeline.

## 3. The Smart Onboarding Workflow

This is the central workflow of the tab, including the mandatory password check for PDFs.

```mermaid
sequenceDiagram
    participant User
    participant UI as Statement Input Tab
    participant Parser as File Parser
    participant DB as DB Interface

    User->>+UI: 1. Uploads a file

    alt Check for PDF Encryption
        UI->>+Parser: 2. IsFileEncrypted(file)
        Parser-->>-UI: 3. Returns True/False
        break If Encrypted
            UI-->>-User: 4a. Prompt for password
            User->>+UI: 5a. Enters password
            UI->>+Parser: 6a. DecryptPDF(file, password)
            Parser-->>-UI: 7a. Returns decrypted file object
        end
    end

    UI->>+Parser: 8. GenerateFingerprint(decrypted_file_or_original)
    Parser-->>-UI: 9. Returns fingerprint

    UI->>+DB: 10. FindAccount(fingerprint=...)
    DB-->>-UI: 11. Returns matching account or None

    alt Known Account
        UI-->>-User: 12a. "File for 'My HDFC Savings' found. Confirm?"
        User->>+UI: 13a. Clicks "Confirm"
        Note over UI: File is ready for processing.
    else Unknown Account
        UI-->>-User: 12b. "This is a new file. Please select or create an account."
        UI->>+DB: 13b. get_accounts_table(only_active=True)
        DB-->>-UI: 14b. Returns list of active accounts
        UI-->>-User: 15b. Renders account selection dropdown and "Add New" button
        
        alt User Selects Existing Account
             User->>+UI: 16a. Selects account from dropdown
             UI->>+DB: 17a. UpdateAccount(fingerprint=...)
             DB-->>-UI: 18a. Success
        else User Creates New Account
             User->>+UI: 16b. Clicks "Add New" and fills form
             UI->>+DB: 17b. save_accounts_table(new_account_with_fingerprint)
             DB-->>-UI: 18b. Success
        end
    end
```

## 4. UI and Component Design

### 4.1. State 1: `AWAITING_UPLOAD`
-   **UI:** A standard `st.file_uploader` is displayed.
-   **Logic:** When a file is uploaded, the component first checks for PDF encryption. If the file is encrypted, it transitions to `AWAITING_PASSWORD`. Otherwise, it proceeds directly to fingerprinting and account lookup, transitioning to the appropriate next state.

### 4.2. State 2: `AWAITING_PASSWORD`
-   **UI:** The file uploader is hidden. The UI displays a simple `st.text_input` for the password and an "Unlock" button.
-   **Logic:** On button click, the system attempts to decrypt the PDF with the provided password. On success, it stores the decrypted file object in session state and proceeds with the fingerprinting/account lookup logic. On failure, it shows an error message.

### 4.3. State 3: `AWAITING_ACCOUNT_SELECTION`
-   **UI:** The file uploader and password input are hidden. The UI displays:
    -   A message: "This looks like a new statement. Please associate it with an account."
    -   An `st.selectbox` populated with all active accounts from `db_interface.get_accounts_table(only_active=True)`.
    -   An "Add New Account" button.
-   **Logic:** Handles the association of a file/fingerprint with a new or existing account, then transitions to `AWAITING_PROCESSING`.

### 4.4. State 4: `AWAITING_PROCESSING`
-   **UI:** All previous inputs are hidden. The UI displays:
    -   A confirmation message: "File for account 'My HDFC Savings' is ready."
    -   A "Process Statement" button.
-   **Logic:** When the user clicks "Process Statement," the file data (decrypted, if necessary) and the selected `account_id` are sent to the main data processing pipeline.

## 5. State Management

-   The entire workflow is orchestrated by a single session state variable, e.g., `st.session_state.upload_flow_state`.
-   Other session state variables will be used to hold the uploaded file data (`st.session_state.uploaded_file_data`) and the determined `account_id` across reruns.

This architecture ensures that no transaction is ever processed without being linked to a specific account, providing a robust and user-friendly data ingestion pipeline.
