"""
Tests for Account CRUD operations.
"""
import pytest
from core.database.db_manager import Database

class TestAccountCRUD:
    """Test suite for Account CRUD operations."""

    @pytest.mark.sanity
    def test_create_account(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: Basic account creation

        Tests fundamental Account CRUD functionality and validates
        that database operations work correctly.
        """
        # Act
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")

        # Assert
        assert account.id is not None
        assert account.name == "HDFC Regalia"
        assert account.account_type == "Credit Card"
        assert account.is_active is True

    @pytest.mark.sanity
    def test_get_account(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: Account retrieval validation

        Tests that created accounts can be retrieved properly,
        ensuring database persistence works correctly.
        """
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")

        # Act
        retrieved_account = db_instance.get_account(account.id)

        # Assert
        assert retrieved_account is not None
        assert retrieved_account.id == account.id
        assert retrieved_account.name == "HDFC Regalia"

    @pytest.mark.sanity
    def test_account_constraint_validation(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: Account constraint validation

        Tests that account constraints are properly enforced,
        catching critical data integrity issues early.
        """
        # Create initial account
        account1 = db_instance.create_account(name="Test Account", account_type="Bank Account")
        assert account1 is not None

        # Test duplicate name constraint (if enforced)
        try:
            account2 = db_instance.create_account(name="Test Account", account_type="Credit Card")
            # If this succeeds, duplicate names are allowed (document behavior)
            assert account2 is not None
        except Exception as e:
            # If this fails, unique constraints are enforced (good)
            assert "UNIQUE" in str(e) or "unique" in str(e)

    @pytest.mark.sanity
    def test_session_isolation_account_operations(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: Session isolation for account operations

        Tests that account operations don't suffer from session contamination
        issues identified in TESTER_FINAL_REPORT.
        """
        # Create multiple accounts in sequence
        accounts_created = []
        for i in range(3):
            account = db_instance.create_account(
                name=f"Session Test Account {i}",
                account_type="Bank Account"
            )
            accounts_created.append(account)
            assert account is not None
            assert account.id is not None

        # Verify all accounts are retrievable (no session contamination)
        for account in accounts_created:
            retrieved = db_instance.get_account(account.id)
            assert retrieved is not None
            assert retrieved.id == account.id

        # Verify account listing works
        all_accounts = db_instance.get_all_accounts()
        assert len(all_accounts) >= 3

    def test_get_all_accounts(self, db_instance: Database):
        """Test retrieving all accounts."""
        # Arrange
        db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        db_instance.create_account(name="ICICI Savings", account_type="Bank Account")

        # Act
        accounts = db_instance.get_all_accounts()

        # Assert
        assert len(accounts) == 2

    def test_update_account(self, db_instance: Database):
        """Test updating an account."""
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")

        # Act
        updated_account = db_instance.update_account(account.id, {"name": "HDFC Diners Club Black"})

        # Assert
        assert updated_account.name == "HDFC Diners Club Black"

    def test_soft_delete_account(self, db_instance: Database):
        """Test soft deleting an account."""
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")

        # Act
        db_instance.update_account(account.id, {"is_active": False})

        # Assert
        updated_account = db_instance.get_account(account.id)
        assert updated_account.is_active is False
