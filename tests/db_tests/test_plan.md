# Database Test Plan

## Overview

This document outlines the test suite for the expenses tracking tool database components. The tests focus on validating the CRUD operations for both Category and Transaction models defined in `core/database/model.py` and implemented in `core/database/crud.py`.

## Test Suite Structure

### Configuration and Fixtures (`conftest.py`)

- **db_engine**: Creates an in-memory SQLite database for isolated testing
- **db_session**: Provides a fresh database session for each test

### Category CRUD Tests (`test_category_crud.py`)

Tests for the Category model CRUD operations:

| Test | Description |
|------|-------------|
| `test_create_category` | Validates creation of a basic category |
| `test_create_category_with_parent` | Tests parent-child relationship creation |
| `test_get_category` | Tests retrieval of a category by ID |
| `test_get_nonexistent_category` | Verifies proper handling when requesting non-existent categories |
| `test_get_all_categories` | Confirms retrieval of all categories |
| `test_update_category` | Tests category update functionality |
| `test_update_nonexistent_category` | Validates behavior when updating non-existent categories |
| `test_delete_category` | Tests category deletion |
| `test_delete_nonexistent_category` | Verifies behavior when deleting non-existent categories |
| `test_category_hierarchy` | Tests parent-child relationship navigation |

### Transaction CRUD Tests (`test_transaction_crud.py`)

Tests for the Transaction model CRUD operations:

| Test | Description |
|------|-------------|
| `test_create_transaction` | Validates creation of a basic transaction |
| `test_create_transaction_with_category` | Tests transaction creation with category association |
| `test_get_transaction` | Tests retrieval of a transaction by ID |
| `test_get_nonexistent_transaction` | Verifies proper handling when requesting non-existent transactions |
| `test_get_all_transactions` | Confirms retrieval of all transactions |
| `test_update_transaction` | Tests transaction update functionality |
| `test_update_transaction_with_category` | Tests updating a transaction's category |
| `test_update_nonexistent_transaction` | Validates behavior when updating non-existent transactions |
| `test_delete_transaction` | Tests transaction deletion |
| `test_delete_nonexistent_transaction` | Verifies behavior when deleting non-existent transactions |
| `test_transaction_category_relationship` | Tests the relationship between transactions and categories |

## Test Coverage

The test suite covers:

1. **Basic CRUD Operations**
   - Create, read, update, and delete operations for both models
   - Edge cases (non-existent records)

2. **Relationships**
   - Category parent-child hierarchies
   - Transaction-category associations

3. **Data Validation**
   - Field value persistence
   - Timestamp handling (created_at, updated_at)

## Test Independence

Tests are designed to:
- Use isolated in-memory SQLite databases
- Create fresh test data for each test case
- Clean up resources after test completion

## Running Tests

Execute the test suite using:

```bash
# Run all database tests
pytest tests/db_tests

# Run with verbose output
pytest -v tests/db_tests

# Run specific test files
pytest tests/db_tests/test_category_crud.py
pytest tests/db_tests/test_transaction_crud.py
```
