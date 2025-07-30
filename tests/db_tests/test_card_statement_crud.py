"""
Tests for CardStatement CRUD operations.
"""
import pytest
import datetime
from core.database.db_manager import Database

class TestCardStatementCRUD:
    """Test suite for CardStatement CRUD operations."""

    def test_create_card_statement(self, db_instance: Database):
        """Test creating a new card statement."""
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        
        # Act
        statement = db_instance.create_card_statement(
            account_id=account.id,
            statement_date=datetime.date(2025, 7, 28),
            total_due=1000.00
        )
        
        # Assert
        assert statement.id is not None
        assert statement.account_id == account.id
        assert statement.total_due == 1000.00

    def test_get_card_statement(self, db_instance: Database):
        """Test retrieving a card statement by ID."""
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        statement = db_instance.create_card_statement(
            account_id=account.id,
            statement_date=datetime.date(2025, 7, 28),
            total_due=1000.00
        )
        
        # Act
        retrieved_statement = db_instance.get_card_statement(statement.id)
        
        # Assert
        assert retrieved_statement is not None
        assert retrieved_statement.id == statement.id

    def test_update_card_statement(self, db_instance: Database):
        """Test updating a card statement."""
        # Arrange
        account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        statement = db_instance.create_card_statement(
            account_id=account.id,
            statement_date=datetime.date(2025, 7, 28),
            total_due=1000.00
        )
        
        # Act
        updated_statement = db_instance.update_card_statement(statement.id, {"total_due": 1200.00})
        
        # Assert
        assert updated_statement.total_due == 1200.00
