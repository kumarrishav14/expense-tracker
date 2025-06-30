"""
Tests for Transaction CRUD operations.
"""
import datetime
import pytest
from sqlalchemy.orm import Session

from core.database import crud
from core.database.model import Transaction, Category


class TestTransactionCRUD:
    """Test suite for Transaction CRUD operations."""

    def test_create_transaction(self, db_session: Session):
        """Test creating a new transaction."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        # Act
        transaction = crud.create_transaction(
            db_session, 
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
        assert transaction.embedding is None

    def test_create_transaction_with_category(self, db_session: Session):
        """Test creating a transaction with a category."""
        # Arrange
        category = crud.create_category(db_session, name="Food")
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        # Act
        transaction = crud.create_transaction(
            db_session, 
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
        assert transaction.created_at is not None

    def test_get_transaction(self, db_session: Session):
        """Test retrieving a transaction by ID."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        transaction = crud.create_transaction(
            db_session, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        # Act
        retrieved_transaction = crud.get_transaction(db_session, transaction.id)
        
        # Assert
        assert retrieved_transaction is not None
        assert retrieved_transaction.id == transaction.id
        assert retrieved_transaction.amount == 100.50
        assert retrieved_transaction.description == "Grocery shopping"

    def test_get_nonexistent_transaction(self, db_session: Session):
        """Test retrieving a non-existent transaction."""
        # Act
        transaction = crud.get_transaction(db_session, 999)
        
        # Assert
        assert transaction is None

    def test_get_all_transactions(self, db_session: Session):
        """Test retrieving all transactions."""
        # Arrange
        date1 = datetime.datetime(2023, 1, 15, 12, 0, 0)
        date2 = datetime.datetime(2023, 1, 16, 12, 0, 0)
        date3 = datetime.datetime(2023, 1, 17, 12, 0, 0)
        
        crud.create_transaction(db_session, amount=100.50, transaction_date=date1, description="Grocery")
        crud.create_transaction(db_session, amount=200.00, transaction_date=date2, description="Electronics")
        crud.create_transaction(db_session, amount=50.75, transaction_date=date3, description="Books")
        
        # Act
        transactions = crud.get_all_transactions(db_session)
        
        # Assert
        assert len(transactions) == 3
        descriptions = [t.description for t in transactions]
        assert "Grocery" in descriptions
        assert "Electronics" in descriptions
        assert "Books" in descriptions

    def test_update_transaction(self, db_session: Session):
        """Test updating a transaction."""
        # Arrange
        original_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        new_date = datetime.datetime(2023, 1, 16, 14, 0, 0)
        
        transaction = crud.create_transaction(
            db_session, 
            amount=100.50, 
            transaction_date=original_date,
            description="Grocery shopping"
        )
        original_created_at = transaction.created_at
        
        # Act
        updated_transaction = crud.update_transaction(
            db_session, 
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

    def test_update_transaction_with_category(self, db_session: Session):
        """Test updating a transaction with a new category."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        transaction = crud.create_transaction(
            db_session, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        category = crud.create_category(db_session, name="Food")
        
        # Act
        updated_transaction = crud.update_transaction(
            db_session, 
            transaction.id, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping",
            category_id=category.id
        )
        
        # Assert
        assert updated_transaction.category_id == category.id

    def test_update_nonexistent_transaction(self, db_session: Session):
        """Test updating a non-existent transaction."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        # Act
        updated_transaction = crud.update_transaction(
            db_session, 
            999, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Nonexistent"
        )
        
        # Assert
        assert updated_transaction is None

    def test_delete_transaction(self, db_session: Session):
        """Test deleting a transaction."""
        # Arrange
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        transaction = crud.create_transaction(
            db_session, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping"
        )
        
        # Act
        result = crud.delete_transaction(db_session, transaction.id)
        
        # Assert
        assert result is True
        assert crud.get_transaction(db_session, transaction.id) is None

    def test_delete_nonexistent_transaction(self, db_session: Session):
        """Test deleting a non-existent transaction."""
        # Act
        result = crud.delete_transaction(db_session, 999)
        
        # Assert
        assert result is False

    def test_transaction_category_relationship(self, db_session: Session):
        """Test the relationship between transactions and categories."""
        # Arrange
        category = crud.create_category(db_session, name="Food")
        transaction_date = datetime.datetime(2023, 1, 15, 12, 0, 0)
        
        transaction = crud.create_transaction(
            db_session, 
            amount=100.50, 
            transaction_date=transaction_date,
            description="Grocery shopping",
            category_id=category.id
        )
        
        # Act
        retrieved_transaction = crud.get_transaction(db_session, transaction.id)
        
        # Assert
        assert retrieved_transaction.category_id == category.id
        assert retrieved_transaction.category.name == "Food"
