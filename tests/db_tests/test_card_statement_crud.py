"""
Tests for CardStatement CRUD operations.
"""
import pytest
import datetime
from core.database.db_manager import Database

class TestCardStatementCRUD:
    """Test suite for CardStatement CRUD operations."""

    @pytest.mark.sanity
    def test_create_card_statement(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: Basic CardStatement creation

        Tests fundamental CardStatement CRUD functionality.
        Critical for detecting basic model and database issues.
        """
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

    @pytest.mark.sanity
    def test_get_card_statement(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: CardStatement retrieval

        Tests basic retrieval functionality to ensure database
        operations work correctly after creation.
        """
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

    @pytest.mark.sanity
    def test_update_card_statement(self, db_instance: Database):
        """
        CRITICAL SANITY TEST: CardStatement update operations

        Tests update functionality which is critical for statement
        status management and payment tracking.
        """
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
