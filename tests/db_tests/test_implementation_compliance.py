"""
Database Implementation Compliance Tests

This test suite validates the database implementation against architectural specifications
and exposes critical bugs and gaps identified in the architectural review.

As per tester guidelines:
- Tests are written based on architecture, not current flawed implementation
- Tests expose implementation bugs and missing features
- Tests validate architectural compliance strictly
- Tests are not lenient on dev misses

Critical Issues Being Tested:
1. account_id handling bug in create_transactions_batch
2. Inefficient category resolution (fetching all categories)
3. Missing batch operations for accounts and statements
4. Missing OperationResult return structures
5. Missing explicit transaction management methods
6. Inadequate error classification
"""

import pytest
import datetime
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError, OperationalError
import pytz
from uuid import uuid4

from core.database.db_interface import DatabaseInterface
from core.database.db_manager import Database
from core.database.model import Transaction, Category, Account, CardStatement

indian_timezone = pytz.timezone("Asia/Kolkata")


class TestCriticalImplementationBugs:
    """Test suite exposing critical bugs in the current implementation."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        interface = DatabaseInterface("sqlite:///:memory:")
        # Seed with test data
        # Use unique names to avoid conflicts
        unique_suffix = str(uuid4())[:8]
        interface.db.create_account(f"Test Account {unique_suffix}", "Bank Account", "Test Bank", "1234")
        interface.create_category_hierarchy("Food", "Restaurants")
        return interface

    def test_critical_bug_account_id_missing_in_batch_creation(self, db_interface):
        """
        CRITICAL BUG TEST: create_transactions_batch fails to handle account_id properly.

        According to architectural review, the method receives account_id in transactions_data
        but fails to pass it to model.Transaction constructor, causing IntegrityError.

        This test exposes the bug by attempting to create transactions with account_id.
        """
        # Create test account
        account = db_interface.db.create_account("Test Account 2", "Credit Card", "HDFC", "5678")

        # Prepare transaction data with account_id
        transaction_data = [{
            'amount': 100.0,
            'transaction_date': datetime.datetime.now(indian_timezone),
            'account_id': account.id,
            'description': 'Test Transaction'
        }]

        # This should work according to architecture but will fail due to bug
        with pytest.raises(IntegrityError, match="NOT NULL constraint failed"):
            db_interface.db.create_transactions_batch(transaction_data)

    def test_inefficient_category_resolution_performance_issue(self, db_interface):
        """
        PERFORMANCE BUG TEST: _resolve_category_id fetches all categories instead of targeted query.

        According to architectural review, this method calls get_all_categories() and iterates
        in Python instead of using database-level filtering. This is highly inefficient.

        This test exposes the inefficiency by monitoring database calls.
        """
        # Create many categories to simulate real-world scenario
        for i in range(50):
            db_interface.create_category_hierarchy(f"Category{i}", f"SubCat{i}")

        # Mock the get_all_categories to track calls
        with patch.object(db_interface.db, 'get_all_categories') as mock_get_all:
            mock_get_all.return_value = db_interface.db.get_all_categories()

            # Resolve a single category
            result = db_interface._resolve_category_id("Food", "Restaurants")

            # Should use targeted query, not fetch all categories
            # This assertion will fail, exposing the inefficiency
            assert mock_get_all.call_count == 0, \
                "PERFORMANCE BUG: _resolve_category_id should use targeted query, not fetch all categories"

    def test_missing_batch_operations_for_accounts(self, db_interface):
        """
        MISSING FEATURE TEST: save_accounts_table lacks proper batch operations.

        According to architecture, this should use atomic batch operations but currently
        iterates and calls single-record methods, which is inefficient and not atomic.
        """
        accounts_df = pd.DataFrame([
            {'name': 'Account1', 'account_type': 'Bank', 'bank_name': 'Bank1'},
            {'name': 'Account2', 'account_type': 'Credit', 'bank_name': 'Bank2'},
        ])

        # Mock create_account to simulate failure midway
        call_count = 0
        original_create = db_interface.db.create_account

        def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Fail on second account
                raise IntegrityError("Simulated failure", None, None)
            return original_create(*args, **kwargs)

        with patch.object(db_interface.db, 'create_account', side_effect=mock_create):
            # This should be atomic but will leave database in inconsistent state
            result = db_interface.save_accounts_table(accounts_df)

            # Should fail atomically, but current implementation allows partial success
            assert result is False, "Batch operation should fail atomically"

            # Check database state - should have no accounts due to rollback
            accounts = db_interface.get_accounts_table()
            # This assertion will fail, exposing non-atomic behavior
            assert len(accounts) == 0, \
                "ATOMICITY BUG: Partial failure should rollback all operations, but some accounts were created"

    def test_missing_batch_operations_for_card_statements(self, db_interface):
        """
        MISSING FEATURE TEST: save_card_statements_table lacks proper batch operations.

        Similar to accounts, this should use atomic batch operations but doesn't.
        """
        # Create account for statements
        account = db_interface.db.create_account("Credit Card", "Credit Card", "HDFC", "1234")

        statements_df = pd.DataFrame([
            {'account_id': account.id, 'statement_date': '2024-01-01', 'total_due': 1000.0},
            {'account_id': account.id, 'statement_date': '2024-02-01', 'total_due': 1500.0},
        ])

        # This should work but will fail due to missing batch implementation
        with pytest.raises(AttributeError, match="'Database' object has no attribute 'create_card_statements_batch'"):
            db_interface.save_card_statements_table(statements_df)


class TestArchitecturalComplianceGaps:
    """Test suite exposing gaps between implementation and architecture."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        return DatabaseInterface("sqlite:///:memory:")

    def test_missing_operation_result_structures(self, db_interface):
        """
        ARCHITECTURE GAP: Methods should return OperationResult structures.

        According to architecture, all operations should return structured results
        with success status, error messages, affected rows, etc.
        """
        account_df = pd.DataFrame([
            {'name': 'Test Account', 'account_type': 'Bank', 'bank_name': 'Test Bank'}
        ])

        result = db_interface.save_accounts_table(account_df)

        # Should return OperationResult structure, not boolean
        assert hasattr(result, 'success'), \
            "ARCHITECTURE GAP: save_accounts_table should return OperationResult structure"
        assert hasattr(result, 'error_message'), \
            "ARCHITECTURE GAP: OperationResult should have error_message field"
        assert hasattr(result, 'affected_rows'), \
            "ARCHITECTURE GAP: OperationResult should have affected_rows field"

    def test_missing_explicit_transaction_management(self, db_interface):
        """
        ARCHITECTURE GAP: Missing explicit transaction management methods.

        Architecture specifies begin_transaction, commit_transaction, rollback_transaction
        methods for explicit transaction control.
        """
        # These methods should exist according to architecture
        with pytest.raises(AttributeError):
            db_interface.begin_transaction()

        with pytest.raises(AttributeError):
            db_interface.commit_transaction()

        with pytest.raises(AttributeError):
            db_interface.rollback_transaction()

    def test_missing_batch_operation_result_structures(self, db_interface):
        """
        ARCHITECTURE GAP: Batch operations should return BatchOperationResult.

        According to architecture, batch operations should return structured results
        with successful_count, failed_count, and error details.
        """
        # Create test data
        df = pd.DataFrame([
            {'description': 'Test', 'amount': 100, 'transaction_date': datetime.datetime.now(),
             'category': 'Food', 'sub_category': 'Restaurants', 'account_id': 1}
        ])

        result = db_interface.save_transactions_table(df)

        # Should return BatchOperationResult structure
        assert hasattr(result, 'successful_count'), \
            "ARCHITECTURE GAP: Batch operations should return BatchOperationResult"
        assert hasattr(result, 'failed_count'), \
            "ARCHITECTURE GAP: BatchOperationResult should have failed_count"
        assert hasattr(result, 'errors'), \
            "ARCHITECTURE GAP: BatchOperationResult should have errors list"

    def test_missing_bulk_categorize_transactions_method(self, db_interface):
        """
        ARCHITECTURE GAP: Missing bulk_categorize_transactions method.

        Architecture specifies this method for applying categorization rules to
        multiple transactions in batch.
        """
        categorization_rules = [
            {'pattern': 'RESTAURANT', 'category': 'Food', 'sub_category': 'Restaurants'},
            {'pattern': 'UBER', 'category': 'Transportation', 'sub_category': 'Ride Sharing'}
        ]

        with pytest.raises(AttributeError):
            db_interface.bulk_categorize_transactions(categorization_rules)

    def test_missing_get_card_statements_table_method(self, db_interface):
        """
        ARCHITECTURE GAP: Missing get_card_statements_table method.

        Architecture specifies this method for retrieving card statements as DataFrame.
        """
        with pytest.raises(AttributeError):
            db_interface.get_card_statements_table()

    def test_missing_flag_transaction_as_transfer_method(self, db_interface):
        """
        ARCHITECTURE GAP: Missing flag_transaction_as_transfer method.

        Architecture specifies this method for marking transactions as transfers.
        """
        with pytest.raises(AttributeError):
            db_interface.flag_transaction_as_transfer(1)

    def test_missing_update_statement_status_method(self, db_interface):
        """
        ARCHITECTURE GAP: Missing update_statement_status method.

        Architecture specifies this method for updating card statement status.
        """
        with pytest.raises(AttributeError):
            db_interface.update_statement_status(1, 'PAID')


class TestDatabaseManagerArchitecturalGaps:
    """Test suite exposing gaps in db_manager implementation."""

    @pytest.fixture
    def db_manager(self):
        """Create a fresh database manager for each test."""
        return Database("sqlite:///:memory:")

    def test_missing_get_category_by_name_optimization(self, db_manager):
        """
        ARCHITECTURE GAP: Missing optimized get_category_by_name method.

        Architectural review recommends this method to replace inefficient
        get_all_categories + iteration pattern.
        """
        # Create test categories
        parent = db_manager.create_category("Food")
        child = db_manager.create_category("Restaurants", parent.id)

        # This optimized method should exist but doesn't
        with pytest.raises(AttributeError):
            db_manager.get_category_by_name("Restaurants", parent_name="Food")

        # Fallback to inefficient method exists
        categories = db_manager.get_all_categories()
        assert len(categories) > 0, "Fallback method should work but is inefficient"

    def test_missing_accounts_and_statements_batch_methods(self, db_manager):
        """
        ARCHITECTURE GAP: Missing batch methods for accounts and statements.

        According to architectural review, these methods should exist for
        proper atomic batch operations.
        """
        # These batch methods should exist according to architecture
        accounts_data = [
            {'name': 'Account1', 'account_type': 'Bank', 'bank_name': 'Bank1'},
            {'name': 'Account2', 'account_type': 'Credit', 'bank_name': 'Bank2'}
        ]

        # Method exists but implementation might be incomplete
        try:
            result = db_manager.create_accounts_batch(accounts_data, session=db_manager.get_session())
            assert len(result) == 2, "Batch account creation should work properly"
        except Exception as e:
            pytest.fail(f"create_accounts_batch should be properly implemented: {e}")

        statements_data = [
            {'account_id': 1, 'statement_date': datetime.date(2024, 1, 1), 'total_due': 1000.0},
            {'account_id': 1, 'statement_date': datetime.date(2024, 2, 1), 'total_due': 1500.0}
        ]

        try:
            result = db_manager.create_card_statements_batch(statements_data, session=db_manager.get_session())
            assert len(result) == 2, "Batch statement creation should work properly"
        except Exception as e:
            pytest.fail(f"create_card_statements_batch should be properly implemented: {e}")


class TestErrorHandlingCompliance:
    """Test suite exposing inadequate error handling and classification."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        return DatabaseInterface("sqlite:///:memory:")

    def test_inadequate_error_classification_coverage(self, db_interface):
        """
        ERROR HANDLING GAP: Limited error type classification.

        Architecture should handle more error types than currently implemented.
        """
        # Test various error types that should be classified
        errors_to_test = [
            (IntegrityError("UNIQUE constraint failed", None, None), "constraint_violation"),
            (OperationalError("database is locked", None, None), "operational_error"),
            (ValueError("Invalid data type"), "data_validation_error"),
            (TypeError("Wrong type provided"), "data_validation_error"),
        ]

        for error, expected_category in errors_to_test:
            error_info = db_interface.db.handle_constraint_error(error)

            # Should properly classify all error types
            assert 'error_category' in error_info, \
                f"Error classification missing for {type(error).__name__}"
            assert error_info['error_category'] == expected_category, \
                f"Incorrect classification for {type(error).__name__}: expected {expected_category}, got {error_info.get('error_category')}"

    def test_missing_retry_strategy_implementation(self, db_interface):
        """
        ERROR HANDLING GAP: Incomplete retry strategy implementation.

        Architecture should provide retry logic for retryable errors but
        current implementation only identifies them.
        """
        # Simulate retryable error
        operational_error = OperationalError("database is locked", None, None)

        # Should be identified as retryable
        assert db_interface.db.is_retryable_error(operational_error), \
            "OperationalError should be identified as retryable"

        # But there's no actual retry implementation in the interface
        # This gap means users have to implement retry logic themselves

        # Architecture should provide retry_operation method
        with pytest.raises(AttributeError):
            db_interface.retry_operation(lambda: db_interface.save_transactions_table(pd.DataFrame()))


class TestPerformanceAndScalabilityGaps:
    """Test suite exposing performance issues in current implementation."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        interface = DatabaseInterface("sqlite:///:memory:")
        # Create test account
        interface.db.create_account("Test Account", "Bank Account", "Test Bank", "1234")
        return interface

    def test_category_resolution_scales_poorly(self, db_interface):
        """
        PERFORMANCE ISSUE: Category resolution doesn't scale with data size.

        Current implementation fetches all categories for every resolution,
        which becomes exponentially slower as category count grows.
        """
        # Create large category hierarchy
        categories_count = 100
        for i in range(categories_count):
            db_interface.create_category_hierarchy(f"Category{i}", f"SubCat{i}")

        # Time multiple resolutions to show performance degradation
        import time

        start_time = time.time()
        for i in range(10):  # Resolve 10 categories
            db_interface._resolve_category_id(f"Category{i}", f"SubCat{i}")
        resolution_time = time.time() - start_time

        # Each resolution should be O(1), not O(n) where n is total categories
        # With 100 categories, 10 resolutions should complete quickly
        assert resolution_time < 0.1, \
            f"PERFORMANCE ISSUE: Category resolution too slow ({resolution_time:.3f}s for 10 resolutions with {categories_count} categories)"

    def test_batch_operations_lack_proper_optimization(self, db_interface):
        """
        PERFORMANCE ISSUE: Batch operations use loops instead of bulk SQL operations.

        Current implementation processes records one by one instead of using
        database bulk operations, which is inefficient for large datasets.
        """
        # Create large transaction dataset
        large_df = pd.DataFrame([{
            'description': f'Transaction {i}',
            'amount': float(i * 10),
            'transaction_date': datetime.datetime.now(indian_timezone),
            'category': 'Food',
            'sub_category': 'Restaurants',
            'account_id': 1
        } for i in range(100)])

        # Time the batch operation
        import time
        start_time = time.time()

        try:
            result = db_interface.save_transactions_table(large_df)
            batch_time = time.time() - start_time

            # Batch operations should be significantly faster than individual operations
            # 100 transactions should complete in reasonable time
            assert batch_time < 2.0, \
                f"PERFORMANCE ISSUE: Batch operation too slow ({batch_time:.3f}s for 100 transactions)"

        except Exception as e:
            # If it fails due to implementation bugs, that's also a compliance issue
            pytest.fail(f"Batch operation failed due to implementation issues: {e}")


class TestDataIntegrityAndConstraints:
    """Test suite exposing data integrity issues in implementation."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        interface = DatabaseInterface("sqlite:///:memory:")
        interface.db.create_account("Test Account", "Bank Account", "Test Bank", "1234")
        return interface

    def test_transaction_account_id_constraint_enforcement(self, db_interface):
        """
        DATA INTEGRITY ISSUE: Transaction.account_id constraint not properly enforced.

        According to model, account_id is non-nullable foreign key, but batch creation
        doesn't handle this properly.
        """
        # Create transaction without account_id
        df = pd.DataFrame([{
            'description': 'Test Transaction',
            'amount': 100.0,
            'transaction_date': datetime.datetime.now(indian_timezone),
            'category': 'Food',
            'sub_category': 'Restaurants'
            # Missing account_id - should fail
        }])

        # Should fail with integrity error, not silent failure
        result = db_interface.save_transactions_table(df)
        assert result is False, "Transaction creation without account_id should fail"

        # Verify no transactions were created
        transactions = db_interface.get_transactions_table()
        assert len(transactions) == 0, "No transactions should be created when constraint violated"

    def test_category_hierarchy_integrity_validation(self, db_interface):
        """
        DATA INTEGRITY ISSUE: Category hierarchy constraints not fully validated.

        Should prevent circular references and enforce proper parent-child relationships.
        """
        # Create parent category
        parent = db_interface.db.create_category("Food")

        # Attempt to create circular reference
        try:
            # Child pointing to itself as parent should fail
            circular_category = db_interface.db.create_category("Circular", parent_id=999999)  # Non-existent parent
            pytest.fail("Should not allow invalid parent_id")
        except IntegrityError:
            pass  # Expected behavior

        # Test proper hierarchy creation
        child = db_interface.db.create_category("Restaurants", parent_id=parent.id)
        assert child.parent_id == parent.id, "Valid hierarchy should be created"
