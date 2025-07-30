"""
Tests for Account CRUD operations.
"""
import pytest
from core.database.db_manager import Database

class TestAccountCRUD:
    """Test suite for Account CRUD operations."""

    def test_create_account(self, db_instance: Database):
        """Test creating a new account."""
        # Act
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        
        # Assert
        assert account.id is not None
        assert account.name == "HDFC Regalia"
        assert account.account_type == "Credit Card"
        assert account.is_active is True

    def test_get_account(self, db_instance: Database):
        """Test retrieving an account by ID."""
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        
        # Act
        retrieved_account = db_instance.get_account(account.id)
        
        # Assert
        assert retrieved_account is not None
        assert retrieved_account.id == account.id
        assert retrieved_account.name == "HDFC Regalia"

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
