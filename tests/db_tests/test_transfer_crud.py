"""
Tests for Transfer CRUD operations and linking logic.
"""
import pytest
import datetime
from core.database.db_manager import Database

class TestTransferCRUD:
    """Test suite for Transfer CRUD operations."""

    def test_create_transfer(self, db_instance: Database):
        """Test creating a new transfer."""
        # Arrange
        bank_account = db_instance.create_account(name="ICICI Savings", account_type="Bank Account")
        cc_account = db_instance.create_account(name="HDFC Regalia", account_type="Credit Card")
        
        payment_transaction = db_instance.create_transaction(
            account_id=bank_account.id,
            amount=-5000.00,
            transaction_date=datetime.datetime(2025, 7, 20),
            description="Credit card payment"
        )
        
        card_statement = db_instance.create_card_statement(
            account_id=cc_account.id,
            statement_date=datetime.date(2025, 7, 15),
            total_due=5000.00
        )
        
        # Act
        transfer = db_instance.create_transfer(
            payment_transaction_id=payment_transaction.id,
            statement_id=card_statement.id
        )
        
        # Assert
        assert transfer.id is not None
        assert transfer.payment_transaction_id == payment_transaction.id
        assert transfer.statement_id == card_statement.id
