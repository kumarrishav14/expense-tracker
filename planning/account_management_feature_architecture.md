# Feature Architecture: Account Management

**Author:** AI Architect
**Date:** July 24, 2025
**Version:** 1.0

## 1. Overview

This document provides the complete architecture for the **Account Management** feature. This is a foundational feature that enables the user to create, manage, and close their financial accounts within the application. 

The architecture is designed to provide a seamless user experience through two primary mechanisms: a **Smart Onboarding** workflow that intelligently detects new accounts during file uploads, and a **Manual Management** UI for direct user control.

## 2. Core Architectural Concepts

### 2.1. Soft Deletion (Active Status)
To preserve historical integrity, accounts are never physically deleted from the database. Instead, they are marked as inactive using an `is_active` flag. This ensures that past transactions remain correctly associated with their original account, while closed accounts are hidden from future operations.

### 2.2. Intelligent File Parsing
The system will use intelligent parsing techniques to identify the source account of an uploaded statement, minimizing user effort.

-   **For CSV Files (Fingerprinting):** The system will generate a unique "fingerprint" based on the CSV's column structure. This allows the application to reliably recognize statements from known accounts.
-   **For PDF Files (Metadata Extraction):** The system will use libraries like `pdfplumber` to scan PDFs for key metadata, such as bank names and the last four digits of an account number. This allows for the smart identification of accounts even from PDF statements.

## 3. Database Schema Impact

This feature requires the following additions to the `accounts` table.

*Reference: [Database Schema Architecture](db_model/schema_architecture.md)*

-   **`accounts` table - Additions:**
    -   `is_active` (BOOLEAN, NOT NULL, Default: `True`): The flag for soft deletion.
    -   `file_fingerprint` (String, Nullable, UNIQUE): Stores the unique hash of a CSV file's format to identify its source account.

## 4. User Workflows

### 4.1. Workflow A: Smart Onboarding (During File Upload)
This workflow is triggered when a user uploads a statement file.

1.  **Intelligent Parsing:** The system parses the file using the appropriate method:
    -   If CSV, it generates a **fingerprint**.
    -   If PDF, it attempts to **extract metadata** (bank name, account number last 4).
2.  **Account Lookup:** It searches for an account matching the extracted data (either the fingerprint or the metadata).
3.  **Scenario A (Known File):** If a confident match is found, the UI confirms the account with the user (e.g., "This looks like a statement for 'My HDFC Regalia'. Correct?"). Upon confirmation, transactions are processed.
4.  **Scenario B (Unknown File):** If no match is found, the UI prompts the user to either select an existing active account or to create a new one. If metadata was successfully extracted from a PDF, the "New Account" form will be **pre-filled** to assist the user.
5.  **Account Creation:** When a new account is created, its `file_fingerprint` (if applicable) is saved along with the other account details.

### 4.2. Workflow B: Manual Management (In Settings)
This workflow is handled in a dedicated "Accounts" section within the application's "Settings" tab.

-   **Create Account:** A user can proactively create a new account at any time using an "Add New Account" button.
-   **Edit Account:** A user can edit the details (`name`, `bank_name`, etc.) of any existing account. This view also allows the user to clear a stored `file_fingerprint` to reset the smart detection for that account.

### 4.3. Workflow C: Closing an Account
This is a specific action within the Manual Management UI.

1.  **User Action:** The user clicks a "Mark as Closed" button next to an active account.
2.  **Confirmation:** A dialog appears, explaining that the account will be hidden from future use but all its historical data will be preserved.
3.  **System Action:** Upon confirmation, the system executes a single, non-destructive `UPDATE` command to set `is_active = False` for that account record.

## 5. High-Level UI and Component Design

-   **Upload Workflow:** The file upload component in the "Statement Input" tab will contain the logic to trigger the Smart Onboarding UI (either the confirmation or the creation prompt).
-   **Settings Tab:** A new "Accounts" sub-section will be added to the Settings tab to house the manual management interface.

## 6. Impact on Other Features

The `is_active` status of an account is critical for other features:

-   **Credit Mapping:** The lists of unpaid bills and potential payments will **only** show items from `active` accounts.
-   **Dashboard & Reporting:** All historical reports and dashboard calculations will use transactions from **all** accounts, regardless of their `is_active` status, to ensure historical accuracy.
-   **Manual Transaction Entry:** Any UI for manually adding transactions must **only** show `active` accounts in the account selection dropdown.

## 7. Smart Onboarding Logic Flow

```mermaid
graph TD
    A[User Uploads File] --> B{Is it a CSV?};
    B -- Yes --> C[Generate Fingerprint];
    B -- No --> D[Extract PDF Metadata];
    
    C --> E{Find Account by Fingerprint};
    D --> F{Find Account by Metadata};

    E -- Match Found --> G{Confirm Account with User};
    F -- Match Found --> G;

    G -- Confirmed --> H[Process Transactions];
    
    E -- No Match --> I[Show "Select/Create Account" UI];
    F -- No Match --> I;
    G -- Incorrect --> I;

    I -- Pre-fill with PDF metadata if available --> J[User Selects/Creates Account];
    J --> H;
```
