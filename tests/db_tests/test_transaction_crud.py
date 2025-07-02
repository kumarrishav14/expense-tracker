"""
Tests for Transaction CRUD operations.
"""
import datetime
import pytest
from core.database.db_manager import Database


class TestTransactionCRUD:
    """Test suite for Transaction CRUD operations."""

    def test_create_transaction(self, db_instance: Database):
        """Test creating a new transaction."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        # Act
        transaction = db_instance.create_transaction(
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        # Assert
        assert transaction.id is not None
        assert transaction.amount == 100.50
        assert transaction.transaction_date == transaction_date
        assert transaction.description == "Grocery shopping"
        assert transaction.category_id is None
        assert transaction.created_at is not None

    def test_create_transaction_with_category(self, db_instance: Database):
        """Test creating a transaction with a category."""
        # Arrange
        category = db_instance.create_category(name="Food")
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        # Act
        transaction = db_instance.create_transaction(
            amount=50.25, 
            transaction_date=transaction_date,
            description="Restaurant dinner", 
            category_id=category.id
        )
        
        # Assert
        assert transaction.id is not None
        assert transaction.amount == 50.25
        assert transaction.description == "Restaurant dinner"
        assert transaction.category_id == category.id

    def test_get_transaction(self, db_instance: Database):
        """Test retrieving a transaction by ID."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        transaction = db_instance.create_transaction(
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        # Act
        retrieved_transaction = db_instance.get_transaction(transaction.id)
        
        # Assert
        assert retrieved_transaction is not None
        assert retrieved_transaction.id == transaction.id
        assert retrieved_transaction.amount == 100.50
        assert retrieved_transaction.description == "Grocery shopping"

    def test_get_nonexistent_transaction(self, db_instance: Database):
        """Test retrieving a non-existent transaction."""
        # Act
        transaction = db_instance.get_transaction(999)
        
        # Assert
        assert transaction is None

    def test_get_all_transactions(self, db_instance: Database):
        """Test retrieving all transactions."""
        # Arrange
        date1 = datetime.datetime(2023, 1, 15, 12, 0, 0)
        date2 = datetime.datetime(2023, 1, 16, 12, 0, 0)
        date3 = datetime.datetime(2023, 1, 17, 12, 0, 0)
        
        db_instance.create_transaction(amount=100.50, transaction_date=date1, description="Grocery")
        db_instance.create_transaction(amount=200.00, transaction_date=date2, description="Electronics")
        db_instance.create_transaction(amount=50.75, transaction_date=date3, description="Books")
        
        # Act
        transactions = db_instance.get_all_transactions()
        
        # Assert
        assert len(transactions) == 3
        descriptions = [t.description for t in transactions]
        assert "Grocery" in descriptions
        assert "Electronics" in descriptions
        assert "Books" in descriptions

    def test_update_transaction(self, db_instance: Database):
        """Test updating a transaction."""
        # Arrange
        original_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        new_date = datetime.datetime(2023, 1, 16, 14, 0, 0)
        
        transaction = db_instance.create_transaction(
            amount=100.50, 
            transaction_date=original_date,
            description="Grocery shopping"
        )
        original_created_at = transaction.created_at
        
        # Act
        updated_transaction = db_instance.update_transaction(
            transaction.id, 
            amount=120.75, 
            transaction_date=new_date,
            description="Updated grocery shopping"
        )
        
        # Assert
        assert updated_transaction.id == transaction.id
        assert updated_transaction.amount == 120.75
        assert updated_transaction.transaction_date == new_date
        assert updated_transaction.description == "Updated grocery shopping"
        assert updated_transaction.created_at == original_created_at
        assert updated_transaction.updated_at >= original_created_at

    def test_update_transaction_with_category(self, db_instance: Database):
        """Test updating a transaction with a new category."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        transaction = db_instance.create_transaction(
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        category = db_instance.create_category(name="Food")
        
        # Act
        updated_transaction = db_instance.update_transaction(
            transaction.id, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping",
            category_id=category.id
        )
        
        # Assert
        assert updated_transaction.category_id == category.id

    def test_update_nonexistent_transaction(self, db_instance: Database):
        """Test updating a non-existent transaction."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        # Act
        updated_transaction = db_instance.update_transaction(
            999, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Nonexistent"
        )
        
        # Assert
        assert updated_transaction is None

    def test_delete_transaction(self, db_instance: Database):
        """Test deleting a transaction."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        transaction = db_instance.create_transaction(
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        # Act
        result = db_instance.delete_transaction(transaction.id)
        
        # Assert
        assert result is True
        assert db_instance.get_transaction(transaction.id) is None

    def test_delete_nonexistent_transaction(self, db_instance: Database):
        """Test deleting a non-existent transaction."""
        # Act
        result = db_instance.delete_transaction(999)
        
        # Assert
        assert result is False

    def test_transaction_category_relationship(self, db_instance: Database):
        """Test the relationship between transactions and categories."""
        # Arrange
        category = db_instance.create_category(name="Food")
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        transaction = db_instance.create_transaction(
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping",
            category_id=category.id
        )
        
        # Act
        retrieved_transaction = db_instance.get_transaction(transaction.id)
        retrieved_category = db_instance.get_category(category.id)
        
        # Assert
        assert retrieved_transaction.category_id == retrieved_category.id
