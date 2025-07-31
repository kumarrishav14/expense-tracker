"""
Tests for Missing DatabaseInterface Methods Required by Architecture

This test suite validates that all methods specified in the database interface architecture
are properly implemented. Tests are written based on architectural specifications,
not current implementation, to expose gaps and missing functionality.

According to the architectural review and specifications, the following methods
are missing or incomplete in the current implementation:

1. save_categories_table() - Missing implementation
2. get_card_statements_table() - Missing implementation
3. flag_transaction_as_transfer() - Missing implementation
4. update_statement_status() - Missing implementation
5. bulk_categorize_transactions() - Missing implementation
6. Explicit transaction management methods
7. OperationResult/BatchOperationResult return structures

These tests will fail until the missing methods are properly implemented
according to architectural specifications.
"""

import pytest
import datetime
import pandas as pd
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import IntegrityError
import pytz

from core.database.db_interface import DatabaseInterface
from core.database.model import Account, Transaction, Category, CardStatement

indian_timezone = pytz.timezone("Asia/Kolkata")


class TestMissingInterfaceMethods:
    """Test suite for methods that should exist per architecture but are missing."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        interface = DatabaseInterface("sqlite:///:memory:")
        # Create test account for transaction tests
        interface.db.create_account("Test Account", "Bank Account", "Test Bank", "1234")
        return interface

    @pytest.mark.sanity
    def test_critical_api_methods_exist(self, db_interface):
        """
        CRITICAL SANITY TEST: API completeness validation

        Tests that all essential architectural methods exist and are callable.
        This is a critical gate to catch missing API methods early.
        """
        # Test 1: Essential batch save methods exist
        methods_that_must_exist = [
            'save_categories_table',
            'save_accounts_table',
            'save_card_statements_table',
            'get_card_statements_table',
            'flag_transaction_as_transfer',
            'update_statement_status',
            'bulk_categorize_transactions'
        ]

        for method_name in methods_that_must_exist:
            assert hasattr(db_interface, method_name), f"CRITICAL: Missing method {method_name}"
            method = getattr(db_interface, method_name)
            assert callable(method), f"CRITICAL: {method_name} is not callable"

    @pytest.mark.sanity
    def test_transaction_management_methods_exist(self, db_interface):
        """
        CRITICAL SANITY TEST: Transaction management API validation

        Tests that explicit transaction management methods exist as required
        by architectural specifications for proper session management.
        """
        transaction_methods = [
            'begin_transaction',
            'commit_transaction',
            'rollback_transaction'
        ]

        for method_name in transaction_methods:
            assert hasattr(db_interface, method_name), f"CRITICAL: Missing transaction method {method_name}"
            method = getattr(db_interface, method_name)
            assert callable(method), f"CRITICAL: {method_name} is not callable"

    @pytest.mark.sanity
    def test_return_type_compliance_critical(self, db_interface):
        """
        CRITICAL SANITY TEST: Return type architectural compliance

        Tests that methods return proper structured types (OperationResult/BatchOperationResult)
        as required by architectural specifications.
        """
        from core.database.results import OperationResult, BatchOperationResult

        # Test single operation methods return OperationResult
        single_op_result = db_interface.create_category_hierarchy("Test", "")
        assert isinstance(single_op_result, OperationResult), f"Expected OperationResult, got {type(single_op_result)}"

        # Test batch operation methods return BatchOperationResult
        test_df = pd.DataFrame({'name': ['Test Category'], 'parent_category': ['']})
        batch_result = db_interface.save_categories_table(test_df)
        assert isinstance(batch_result, BatchOperationResult), f"Expected BatchOperationResult, got {type(batch_result)}"

    def test_save_categories_table_method_exists(self, db_interface):
        """
        Test that save_categories_table method exists and works per architecture.

        Architecture specifies this method should:
        - Accept DataFrame with category data
        - Return OperationResult structure
        - Handle batch category creation atomically
        """
        categories_df = pd.DataFrame([
            {'name': 'Food', 'parent_category': None},
            {'name': 'Restaurants', 'parent_category': 'Food'},
            {'name': 'Transportation', 'parent_category': None},
            {'name': 'Uber', 'parent_category': 'Transportation'}
        ])

        # Method should exist
        assert hasattr(db_interface, 'save_categories_table'), \
            "save_categories_table method missing from DatabaseInterface"

        # Should return OperationResult structure
        result = db_interface.save_categories_table(categories_df)

        # Architecture specifies OperationResult structure
        assert hasattr(result, 'success'), "Result should have success field"
        assert hasattr(result, 'error_message'), "Result should have error_message field"
        assert hasattr(result, 'affected_rows'), "Result should have affected_rows field"
        assert hasattr(result, 'error_type'), "Result should have error_type field"

        # Should successfully create categories
        assert result.success is True, "Category creation should succeed"
        assert result.affected_rows == 4, "Should create 4 categories"
        assert result.error_message is None, "No error message on success"

        # Verify categories were created with proper hierarchy
        categories_table = db_interface.get_categories_table()
        assert len(categories_table) == 4, "Should have 4 categories in table"

        # Verify hierarchy is correct
        food_rows = categories_table[categories_table['name'] == 'Food']
        assert len(food_rows) == 1, "Should have Food category"
        assert pd.isna(food_rows.iloc[0]['parent_category']), "Food should have no parent"

        restaurant_rows = categories_table[categories_table['name'] == 'Restaurants']
        assert len(restaurant_rows) == 1, "Should have Restaurants category"
        assert restaurant_rows.iloc[0]['parent_category'] == 'Food', "Restaurants should have Food as parent"

    def test_save_categories_table_handles_errors(self, db_interface):
        """Test save_categories_table error handling per architecture."""
        # Create duplicate category scenario
        db_interface.create_category_hierarchy('Food', '')

        categories_df = pd.DataFrame([
            {'name': 'Food', 'parent_category': None},  # Duplicate
            {'name': 'Transportation', 'parent_category': None}
        ])

        result = db_interface.save_categories_table(categories_df)

        # Should handle error gracefully
        assert result.success is False, "Should fail on duplicate categories"
        assert result.error_message is not None, "Should provide error message"
        assert 'constraint' in result.error_message.lower() or 'duplicate' in result.error_message.lower(), \
            "Error message should indicate constraint violation"
        assert result.error_type in ['IntegrityError', 'constraint_violation'], \
            "Should classify error type correctly"

    def test_get_card_statements_table_method_exists(self, db_interface):
        """
        Test that get_card_statements_table method exists per architecture.

        Architecture specifies this method should:
        - Return DataFrame with card statement data
        - Include columns: account_name, statement_date, total_due, status
        - Handle empty results gracefully
        """
        # Method should exist
        assert hasattr(db_interface, 'get_card_statements_table'), \
            "get_card_statements_table method missing from DatabaseInterface"

        # Should return DataFrame with correct schema
        statements_df = db_interface.get_card_statements_table()

        expected_columns = ['id', 'account_name', 'statement_date', 'total_due', 'status', 'start_date', 'end_date']
        for col in expected_columns:
            assert col in statements_df.columns, f"Missing column {col} in statements DataFrame"

        # Should handle empty case
        assert isinstance(statements_df, pd.DataFrame), "Should return DataFrame"
        assert len(statements_df) == 0, "Should be empty when no statements exist"

    def test_get_card_statements_table_with_data(self, db_interface):
        """Test get_card_statements_table with actual data."""
        # Create credit card account
        account = db_interface.db.create_account("HDFC Regalia", "Credit Card", "HDFC", "5678")

        # Create card statements
        stmt1 = db_interface.db.create_card_statement(
            account.id,
            datetime.date(2024, 1, 15),
            total_due=5000.0,
            status='UNPAID'
        )
        stmt2 = db_interface.db.create_card_statement(
            account.id,
            datetime.date(2024, 2, 15),
            total_due=3500.0,
            status='PAID'
        )

        statements_df = db_interface.get_card_statements_table()

        # Should return proper data
        assert len(statements_df) == 2, "Should return 2 statements"
        assert statements_df['account_name'].iloc[0] == "HDFC Regalia", "Should include account name"
        assert statements_df['total_due'].iloc[0] == 5000.0, "Should include total due amount"
        assert statements_df['status'].iloc[0] == 'UNPAID', "Should include status"

    def test_flag_transaction_as_transfer_method_exists(self, db_interface):
        """
        Test that flag_transaction_as_transfer method exists per architecture.

        Architecture specifies this method should:
        - Accept transaction_id parameter
        - Return OperationResult structure
        - Mark transaction as transfer and update is_transfer flag
        """
        # Create test transaction
        df = pd.DataFrame([{
            'description': 'Payment to Credit Card',
            'amount': -5000.0,
            'transaction_date': datetime.datetime.now(indian_timezone),
            'category': 'Financial',
            'sub_category': 'Transfer',
            'account_id': 1
        }])

        db_interface.save_transactions_table(df)
        transactions = db_interface.get_transactions_table()
        transaction_id = 1  # Assuming first transaction gets ID 1

        # Method should exist
        assert hasattr(db_interface, 'flag_transaction_as_transfer'), \
            "flag_transaction_as_transfer method missing from DatabaseInterface"

        # Should return OperationResult structure
        result = db_interface.flag_transaction_as_transfer(transaction_id)

        assert hasattr(result, 'success'), "Result should have success field"
        assert hasattr(result, 'error_message'), "Result should have error_message field"
        assert hasattr(result, 'affected_rows'), "Result should have affected_rows field"

        # Should successfully flag transaction
        assert result.success is True, "Should successfully flag transaction as transfer"
        assert result.affected_rows == 1, "Should affect 1 transaction"

        # Verify transaction is flagged as transfer
        updated_transaction = db_interface.db.get_transaction(transaction_id)
        assert updated_transaction.is_transfer is True, "Transaction should be flagged as transfer"

    def test_flag_transaction_as_transfer_handles_invalid_id(self, db_interface):
        """Test flag_transaction_as_transfer with invalid transaction ID."""
        result = db_interface.flag_transaction_as_transfer(99999)  # Non-existent ID

        assert result.success is False, "Should fail for non-existent transaction"
        assert result.error_message is not None, "Should provide error message"
        assert 'not found' in result.error_message.lower(), "Should indicate transaction not found"

    def test_update_statement_status_method_exists(self, db_interface):
        """
        Test that update_statement_status method exists per architecture.

        Architecture specifies this method should:
        - Accept statement_id and new_status parameters
        - Return OperationResult structure
        - Update statement status (UNPAID -> PAID, etc.)
        """
        # Create test statement
        account = db_interface.db.create_account("Credit Card", "Credit Card", "HDFC", "1234")
        statement = db_interface.db.create_card_statement(
            account.id,
            datetime.date(2024, 1, 15),
            total_due=5000.0,
            status='UNPAID'
        )

        # Method should exist
        assert hasattr(db_interface, 'update_statement_status'), \
            "update_statement_status method missing from DatabaseInterface"

        # Should return OperationResult structure
        result = db_interface.update_statement_status(statement.id, 'PAID')

        assert hasattr(result, 'success'), "Result should have success field"
        assert hasattr(result, 'error_message'), "Result should have error_message field"
        assert hasattr(result, 'affected_rows'), "Result should have affected_rows field"

        # Should successfully update status
        assert result.success is True, "Should successfully update statement status"
        assert result.affected_rows == 1, "Should affect 1 statement"

        # Verify status was updated
        updated_statement = db_interface.db.get_card_statement(statement.id)
        assert updated_statement.status == 'PAID', "Statement status should be updated to PAID"

    def test_update_statement_status_handles_invalid_id(self, db_interface):
        """Test update_statement_status with invalid statement ID."""
        result = db_interface.update_statement_status(99999, 'PAID')  # Non-existent ID

        assert result.success is False, "Should fail for non-existent statement"
        assert result.error_message is not None, "Should provide error message"
        assert 'not found' in result.error_message.lower(), "Should indicate statement not found"

    def test_bulk_categorize_transactions_method_exists(self, db_interface):
        """
        Test that bulk_categorize_transactions method exists per architecture.

        Architecture specifies this method should:
        - Accept categorization rules (pattern matching)
        - Return BatchOperationResult structure
        - Apply categories to matching transactions in batch
        """
        # Create test transactions
        df = pd.DataFrame([
            {
                'description': 'SWIGGY RESTAURANT PAYMENT',
                'amount': -850.0,
                'transaction_date': datetime.datetime.now(indian_timezone),
                'category': '',
                'sub_category': '',
                'account_id': 1
            },
            {
                'description': 'UBER TRIP BANGALORE',
                'amount': -250.0,
                'transaction_date': datetime.datetime.now(indian_timezone),
                'category': '',
                'sub_category': '',
                'account_id': 1
            },
            {
                'description': 'AMAZON PURCHASE',
                'amount': -1200.0,
                'transaction_date': datetime.datetime.now(indian_timezone),
                'category': '',
                'sub_category': '',
                'account_id': 1
            }
        ])

        db_interface.save_transactions_table(df)

        # Define categorization rules
        categorization_rules = [
            {'pattern': 'SWIGGY', 'category': 'Food', 'sub_category': 'Restaurants'},
            {'pattern': 'UBER', 'category': 'Transportation', 'sub_category': 'Ride Sharing'},
            {'pattern': 'AMAZON', 'category': 'Personal Spending', 'sub_category': 'Shopping'}
        ]

        # Method should exist
        assert hasattr(db_interface, 'bulk_categorize_transactions'), \
            "bulk_categorize_transactions method missing from DatabaseInterface"

        # Should return BatchOperationResult structure
        result = db_interface.bulk_categorize_transactions(categorization_rules)

        assert hasattr(result, 'success'), "Result should have success field"
        assert hasattr(result, 'successful_count'), "Result should have successful_count field"
        assert hasattr(result, 'failed_count'), "Result should have failed_count field"
        assert hasattr(result, 'errors'), "Result should have errors field"

        # Should successfully categorize transactions
        assert result.success is True, "Should successfully categorize transactions"
        assert result.successful_count == 3, "Should categorize 3 transactions"
        assert result.failed_count == 0, "Should have no failures"

        # Verify transactions were categorized
        transactions = db_interface.get_transactions_table()
        swiggy_tx = transactions[transactions['description'].str.contains('SWIGGY')].iloc[0]
        assert swiggy_tx['category'] == 'Food', "SWIGGY transaction should be categorized as Food"
        assert swiggy_tx['sub_category'] == 'Restaurants', "Should have Restaurants sub-category"

        uber_tx = transactions[transactions['description'].str.contains('UBER')].iloc[0]
        assert uber_tx['category'] == 'Transportation', "UBER transaction should be categorized as Transportation"

    def test_bulk_categorize_transactions_handles_errors(self, db_interface):
        """Test bulk_categorize_transactions error handling."""
        # Create transaction with invalid category reference
        df = pd.DataFrame([{
            'description': 'TEST TRANSACTION',
            'amount': -100.0,
            'transaction_date': datetime.datetime.now(indian_timezone),
            'category': '',
            'sub_category': '',
            'account_id': 1
        }])

        db_interface.save_transactions_table(df)

        # Rules with invalid category
        categorization_rules = [
            {'pattern': 'TEST', 'category': 'NonExistentCategory', 'sub_category': 'InvalidSubCategory'}
        ]

        result = db_interface.bulk_categorize_transactions(categorization_rules)

        # Should handle error gracefully
        assert result.successful_count == 0, "Should have no successful categorizations"
        assert result.failed_count == 1, "Should have 1 failed categorization"
        assert len(result.errors) == 1, "Should report 1 error"
        assert 'category' in result.errors[0]['error_message'].lower(), \
            "Error should mention category issue"


class TestExplicitTransactionManagement:
    """Test suite for explicit transaction management methods."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        return DatabaseInterface("sqlite:///:memory:")

    def test_begin_transaction_method_exists(self, db_interface):
        """Test that begin_transaction method exists per architecture."""
        assert hasattr(db_interface, 'begin_transaction'), \
            "begin_transaction method missing from DatabaseInterface"

        # Should return transaction context or ID
        transaction_id = db_interface.begin_transaction()
        assert transaction_id is not None, "Should return transaction identifier"

    def test_commit_transaction_method_exists(self, db_interface):
        """Test that commit_transaction method exists per architecture."""
        assert hasattr(db_interface, 'commit_transaction'), \
            "commit_transaction method missing from DatabaseInterface"

        transaction_id = db_interface.begin_transaction()

        # Should return OperationResult
        result = db_interface.commit_transaction(transaction_id)
        assert hasattr(result, 'success'), "Should return OperationResult structure"
        assert result.success is True, "Should successfully commit transaction"

    def test_rollback_transaction_method_exists(self, db_interface):
        """Test that rollback_transaction method exists per architecture."""
        assert hasattr(db_interface, 'rollback_transaction'), \
            "rollback_transaction method missing from DatabaseInterface"

        transaction_id = db_interface.begin_transaction()

        # Should return OperationResult
        result = db_interface.rollback_transaction(transaction_id)
        assert hasattr(result, 'success'), "Should return OperationResult structure"
        assert result.success is True, "Should successfully rollback transaction"

    def test_explicit_transaction_workflow(self, db_interface):
        """Test complete explicit transaction management workflow."""
        # Begin transaction
        tx_id = db_interface.begin_transaction()

        # Perform operations within transaction
        categories_df = pd.DataFrame([
            {'name': 'Food', 'parent_category': None},
            {'name': 'Restaurants', 'parent_category': 'Food'}
        ])

        result = db_interface.save_categories_table(categories_df, transaction_id=tx_id)
        assert result.success is True, "Operations within transaction should succeed"

        # Commit transaction
        commit_result = db_interface.commit_transaction(tx_id)
        assert commit_result.success is True, "Transaction commit should succeed"

        # Verify data was persisted
        categories = db_interface.get_categories_table()
        assert len(categories) == 2, "Categories should be persisted after commit"

    def test_explicit_transaction_rollback_workflow(self, db_interface):
        """Test explicit transaction rollback workflow."""
        # Begin transaction
        tx_id = db_interface.begin_transaction()

        # Perform operations within transaction
        categories_df = pd.DataFrame([
            {'name': 'Food', 'parent_category': None}
        ])

        result = db_interface.save_categories_table(categories_df, transaction_id=tx_id)
        assert result.success is True, "Operations within transaction should succeed"

        # Rollback transaction
        rollback_result = db_interface.rollback_transaction(tx_id)
        assert rollback_result.success is True, "Transaction rollback should succeed"

        # Verify data was not persisted
        categories = db_interface.get_categories_table()
        assert len(categories) == 0, "Categories should not be persisted after rollback"


class TestReturnStructureCompliance:
    """Test suite ensuring all methods return proper structures per architecture."""

    @pytest.fixture
    def db_interface(self):
        """Create a fresh database interface for each test."""
        interface = DatabaseInterface("sqlite:///:memory:")
        interface.db.create_account("Test Account", "Bank Account", "Test Bank", "1234")
        return interface

    def test_save_transactions_table_returns_batch_operation_result(self, db_interface):
        """Test that save_transactions_table returns BatchOperationResult per architecture."""
        df = pd.DataFrame([
            {
                'description': 'Test Transaction 1',
                'amount': 100.0,
                'transaction_date': datetime.datetime.now(indian_timezone),
                'category': 'Food',
                'sub_category': 'Restaurants',
                'account_id': 1
            },
            {
                'description': 'Test Transaction 2',
                'amount': 200.0,
                'transaction_date': datetime.datetime.now(indian_timezone),
                'category': 'Transportation',
                'sub_category': 'Fuel',
                'account_id': 1
            }
        ])

        result = db_interface.save_transactions_table(df)

        # Should return BatchOperationResult structure, not boolean
        assert hasattr(result, 'success'), "Should return BatchOperationResult with success field"
        assert hasattr(result, 'successful_count'), "Should have successful_count field"
        assert hasattr(result, 'failed_count'), "Should have failed_count field"
        assert hasattr(result, 'errors'), "Should have errors field"
        assert hasattr(result, 'total_processed'), "Should have total_processed field"

        # Should properly populate fields
        assert result.success is True, "Operation should succeed"
        assert result.successful_count == 2, "Should process 2 transactions successfully"
        assert result.failed_count == 0, "Should have no failures"
        assert result.total_processed == 2, "Should process 2 transactions total"
        assert len(result.errors) == 0, "Should have no errors"

    def test_save_accounts_table_returns_operation_result(self, db_interface):
        """Test that save_accounts_table returns OperationResult per architecture."""
        df = pd.DataFrame([
            {'name': 'New Account', 'account_type': 'Bank', 'bank_name': 'Test Bank'}
        ])

        result = db_interface.save_accounts_table(df)

        # Should return OperationResult structure, not boolean
        assert hasattr(result, 'success'), "Should return OperationResult with success field"
        assert hasattr(result, 'error_message'), "Should have error_message field"
        assert hasattr(result, 'error_type'), "Should have error_type field"
        assert hasattr(result, 'affected_rows'), "Should have affected_rows field"

        # Should properly populate fields
        assert result.success is True, "Operation should succeed"
        assert result.affected_rows == 1, "Should affect 1 row"
        assert result.error_message is None, "Should have no error message on success"

    def test_link_transfer_returns_operation_result(self, db_interface):
        """Test that link_transfer returns OperationResult per architecture."""
        # Create test data
        account = db_interface.db.create_account("Credit Card", "Credit Card", "HDFC", "5678")
        statement = db_interface.db.create_card_statement(account.id, datetime.date(2024, 1, 15), 5000.0)

        payment_tx = db_interface.db.create_transaction(
            amount=-5000.0,
            transaction_date=datetime.datetime.now(indian_timezone),
            account_id=1,  # Bank account
            description='Credit Card Payment'
        )

        result = db_interface.link_transfer(payment_tx.id, statement.id)

        # Should return OperationResult structure, not boolean
        assert hasattr(result, 'success'), "Should return OperationResult with success field"
        assert hasattr(result, 'error_message'), "Should have error_message field"
        assert hasattr(result, 'affected_rows'), "Should have affected_rows field"

        # Should properly populate fields
        assert result.success is True, "Operation should succeed"
        assert result.affected_rows >= 1, "Should affect at least 1 row"
        assert result.error_message is None, "Should have no error message on success"
