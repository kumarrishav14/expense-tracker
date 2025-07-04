# Database Test Plan

## Overview

This document outlines the test suite for the expenses tracking tool database components. The tests focus on validating the CRUD operations for both Category and Transaction models defined in `core/database/model.py` and implemented in `core/database/db_manager.py`.

## Test Suite Structure

### Configuration and Fixtures (`conftest.py`)

- **db_instance**: Provides a clean, isolated `Database` manager instance for each test function, connected to an in-memory SQLite database. This ensures test independence and proper resource cleanup.

### Category CRUD Tests (`test_category_crud.py`)

Tests for the Category model CRUD operations with enhanced transaction management:

| Test Category | Tests | Description |
|---------------|-------|-------------|
| **Basic CRUD Operations** | `test_create_category` | Validates creation of a basic category |
| | `test_create_category_with_parent` | Tests parent-child relationship creation |
| | `test_get_category` | Tests retrieval of a category by ID |
| | `test_get_nonexistent_category` | Verifies proper handling when requesting non-existent categories |
| | `test_get_all_categories` | Confirms retrieval of all categories |
| | `test_update_category` | Tests category update functionality |
| | `test_update_nonexistent_category` | Validates behavior when updating non-existent categories |
| | `test_delete_category` | Tests category deletion |
| | `test_delete_nonexistent_category` | Verifies behavior when deleting non-existent categories |
| | `test_category_hierarchy` | Tests multi-level and multiple-child category hierarchy relationships |
| **Transaction Management** | `test_transaction_scope_success` | Tests successful operations within transaction_scope context manager |
| | `test_transaction_scope_rollback_on_error` | Tests automatic rollback when errors occur in transaction |
| | `test_session_parameter_in_crud_operations` | Tests session parameter support in all CRUD methods |
| **Batch Operations** | `test_create_categories_batch_success` | Tests successful batch creation of multiple categories |
| | `test_create_categories_batch_with_hierarchy` | Tests batch creation with parent-child relationships |
| | `test_create_categories_batch_empty_list` | Tests batch operations with empty input |
| | `test_create_categories_batch_within_transaction` | Tests batch operations within transaction scope |
| **Enhanced Queries** | `test_get_categories_by_parent_root_categories` | Tests retrieval of root categories (no parent) |
| | `test_get_categories_by_parent_specific_parent` | Tests retrieval of categories with specific parent |
| | `test_get_categories_by_parent_nonexistent_parent` | Tests query with non-existent parent ID |
| **Error Handling** | `test_handle_constraint_error_integrity_error` | Tests constraint error classification for integrity violations |
| | `test_handle_constraint_error_foreign_key_error` | Tests foreign key constraint error handling |
| | `test_is_retryable_error_operational_error` | Tests retryable error detection for operational errors |
| | `test_is_retryable_error_other_errors` | Tests error classification for various error types |

### Transaction CRUD Tests (`test_transaction_crud.py`)

Tests for the Transaction model CRUD operations with enhanced transaction management:

| Test Category | Tests | Description |
|---------------|-------|-------------|
| **Basic CRUD Operations** | `test_create_transaction` | Validates creation of a basic transaction |
| | `test_create_transaction_with_category` | Tests transaction creation with category association |
| | `test_get_transaction` | Tests retrieval of a transaction by ID |
| | `test_get_nonexistent_transaction` | Verifies proper handling when requesting non-existent transactions |
| | `test_get_all_transactions` | Confirms retrieval of all transactions |
| | `test_update_transaction` | Tests transaction update functionality |
| | `test_update_transaction_with_category` | Tests updating a transaction's category |
| | `test_update_nonexistent_transaction` | Validates behavior when updating non-existent transactions |
| | `test_delete_transaction` | Tests transaction deletion |
| | `test_delete_nonexistent_transaction` | Verifies behavior when deleting non-existent transactions |
| | `test_transaction_category_relationship` | Tests the lazy-loaded relationship between transactions and categories |
| **Transaction Management** | `test_transaction_scope_success_with_transactions` | Tests successful transaction operations within transaction_scope |
| | `test_session_parameter_in_transaction_crud_operations` | Tests session parameter support in all transaction CRUD methods |
| **Batch Operations** | `test_create_transactions_batch_success` | Tests successful batch creation of multiple transactions |
| | `test_create_transactions_batch_empty_list` | Tests batch operations with empty input |
| | `test_create_transactions_batch_within_transaction` | Tests batch operations within transaction scope |
| **Enhanced Queries** | `test_get_transactions_filtered_by_date_range` | Tests filtering transactions by date range |
| | `test_get_transactions_filtered_by_categories` | Tests filtering transactions by category names |
| | `test_get_transactions_filtered_by_amount_range` | Tests filtering transactions by amount range |

### Database Interface Tests (`test_db_interface.py`)

Tests for the DatabaseInterface class that acts as an interface between pandas DataFrames and database tables:

| Test Category | Tests | Description |
|---------------|-------|-------------|
| **Category Table Operations** | `test_get_categories_table_empty` | Validates retrieval of empty categories table |
| | `test_get_categories_table_simple_categories` | Tests retrieval of simple categories without hierarchy |
| | `test_get_categories_table_with_hierarchy` | Tests retrieval of categories with parent-child relationships |
| **Transaction Table Operations** | `test_get_transactions_table_empty` | Validates retrieval of empty transactions table |
| | `test_get_transactions_table_without_categories` | Tests transactions without category assignments |
| | `test_get_transactions_table_with_parent_categories_only` | Tests transactions with top-level categories |
| | `test_get_transactions_table_with_sub_categories` | Tests transactions with sub-categories (parent-child) |
| | `test_get_transactions_table_mixed_categories` | Tests mix of top-level and sub-categories |
| **Category Resolution** | `test_resolve_category_id_*` | Tests internal category ID resolution methods |
| **Category Hierarchy Creation** | `test_create_category_hierarchy_*` | Tests auto-creation of category hierarchies |
| **Transaction Saving** | `test_save_transactions_table_*` | Tests saving DataFrames to database with various scenarios |
| **Real-World Scenarios** | `test_realistic_csv_import_with_errors_and_retry_creates_duplicates` | CSV import with errors, user fixes and re-imports entire file |
| | `test_realistic_batch_processing_failure_and_full_retry` | Batch processing fails partway, entire batch retried |
| | `test_realistic_user_workflow_multiple_import_attempts` | User makes multiple import attempts with incremental fixes |
| | `test_realistic_concurrent_user_scenario_same_data` | Same data imported from multiple sources |
| | `test_realistic_data_validation_edge_cases_with_duplicates` | Edge case data validation leading to duplicates |
| **Enhanced Atomic Transactions** | `test_atomic_transaction_save_success` | Tests successful atomic transaction operations |
| | `test_atomic_transaction_rollback_on_error` | Tests complete rollback on transaction errors |
| | `test_atomic_transaction_with_category_creation` | Tests atomic transaction with automatic category hierarchy creation |
| | `test_session_aware_category_resolution` | Tests category resolution within session context |
| | `test_create_category_hierarchy_in_session` | Tests category hierarchy creation within session |
| | `test_create_category_hierarchy_in_session_with_existing_parent` | Tests hierarchy creation with existing parent categories |
| **Enhanced Error Handling** | `test_error_handling_with_constraint_classification` | Tests constraint error classification |
| | `test_retryable_error_detection` | Tests retryable vs non-retryable error detection |
| | `test_save_transactions_with_detailed_error_logging` | Tests detailed error information and logging |
| | `test_empty_dataframe_handling` | Tests graceful handling of empty DataFrames |
| | `test_missing_required_columns_error_handling` | Tests error handling for missing required columns |
| **Session-Aware Operations** | `test_get_categories_table_with_session_isolation` | Tests category retrieval with session isolation |
| | `test_get_transactions_table_with_session_isolation` | Tests transaction retrieval with session isolation |
| **Batch Operations with Atomic Transactions** | `test_large_batch_atomic_operation` | Tests atomic operations with large batches (50 transactions) |
| | `test_mixed_category_hierarchy_atomic_creation` | Tests atomic creation of complex category hierarchies |
| **Integration & Workflow** | `test_full_workflow_categories_and_transactions` | End-to-end workflow testing |
| | `test_interface_isolation_from_sql_details` | Validates SQL complexity isolation |

## Test Coverage

The test suite covers:

1. **Basic CRUD Operations**
   - Create, read, update, and delete operations for both models
   - Edge cases (non-existent records)

2. **Relationships**
   - Category parent-child hierarchies (multi-level and multiple-child)
   - Transaction-category associations
   - Lazy-loaded relationships

3. **Data Validation**
   - Field value persistence
   - Timestamp handling (created_at, updated_at)

4. **Database Interface Operations**
   - Pandas DataFrame to SQL conversion with atomic transactions
   - SQL to pandas DataFrame conversion with session isolation
   - Category and sub-category denormalization
   - Auto-creation of category hierarchies within atomic transactions
   - Interface isolation from SQL complexity
   - Mixed datetime format handling
   - Partial failure scenarios with complete rollback

5. **Enhanced Transaction Management**
   - Transaction scope context manager with automatic rollback
   - Session parameter support across all CRUD operations
   - Atomic operations with proper commit/rollback handling
   - Error classification and retryable error detection

6. **Batch Operations**
   - Atomic batch creation of categories and transactions
   - Batch operations within transaction scopes
   - Empty input handling and validation
   - Mixed category assignments in batch operations
   - Large-scale batch processing (50+ transactions)

7. **Advanced Query Capabilities**
   - Category hierarchy queries (root categories, children by parent)
   - Transaction filtering by date range, categories, and amount
   - Combined filter criteria support
   - Enhanced relationship querying

8. **Enhanced Database Interface Features**
   - Atomic transaction support for reliable data operations
   - Session-aware category resolution and hierarchy creation
   - Comprehensive error handling with constraint classification
   - Retryable error detection for operational resilience
   - Complete rollback on transaction failures
   - Session isolation for concurrent operations
   - Complex category hierarchy atomic creation
   - Enhanced debugging and error logging

## Test Independence

Tests are designed to:
- Use isolated in-memory SQLite databases
- Create fresh test data for each test case
- Clean up resources after test completion

## Running Tests

Execute the test suite using:

```bash
# Run all database tests
uv run pytest tests/db_tests

# Run with verbose output
uv run pytest -v tests/db_tests

# Run specific test files
uv run pytest tests/db_tests/test_category_crud.py
uv run pytest tests/db_tests/test_transaction_crud.py
uv run pytest tests/db_tests/test_db_interface.py

# Run with coverage report
uv run pytest --cov=core.database tests/db_tests
```