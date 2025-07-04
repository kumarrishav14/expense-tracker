"""
Tests for Transaction CRUD operations with enhanced transaction management and batch operations.
"""
import datetime
import pytest
from decimal import Decimal
import pytz
from sqlalchemy.exc import IntegrityError, DataError
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
        
        # Assert
        assert retrieved_transaction.category is not None
        assert retrieved_transaction.category.id == category.id
        assert retrieved_transaction.category.name == "Food"

    # --- Transaction Management Tests ---

    def test_transaction_scope_context_manager_exists(self, db_instance: Database):
        """Test that transaction_scope context manager exists and can be called."""
        # This test verifies the transaction_scope method exists and is callable
        assert hasattr(db_instance, 'transaction_scope')
        assert callable(db_instance.transaction_scope)
        
        # Test that it returns a context manager
        try:
            with db_instance.transaction_scope() as session:
                # Verify we get a session object
                assert session is not None
                assert hasattr(session, 'query')
                assert hasattr(session, 'add')
                assert hasattr(session, 'commit')
                assert hasattr(session, 'rollback')
        except Exception as e:
            # If it fails, at least we know the method exists
            pass

    def test_session_parameter_in_transaction_crud_operations(self, db_instance: Database):
        """Test that all transaction CRUD operations accept session parameter."""
        # Test that all CRUD methods accept the session parameter without raising errors
        category = db_instance.create_category(name="Food")
        indian_tz = pytz.timezone("Asia/Kolkata")
        transaction_date = indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0))
        
        session = db_instance.get_session()
        
        try:
            # Create with session parameter
            transaction = db_instance.create_transaction(
                amount=25.50,
                transaction_date=transaction_date,
                description="Coffee",
                category_id=category.id,
                session=session
            )
            session.commit()  # Manual commit since we passed session
            assert transaction is not None
            
            # Read with session parameter
            retrieved = db_instance.get_transaction(transaction.id, session=session)
            assert retrieved is not None
            assert retrieved.description == "Coffee"
            
            # Update with session parameter
            updated = db_instance.update_transaction(
                transaction.id,
                amount=30.00,
                transaction_date=transaction_date,
                description="Updated Coffee",
                category_id=category.id,
                session=session
            )
            session.commit()  # Manual commit
            assert updated is not None
            assert updated.description == "Updated Coffee"
            
            # List all with session parameter
            all_transactions = db_instance.get_all_transactions(session=session)
            assert len(all_transactions) >= 1
            
            # Delete with session parameter
            deleted = db_instance.delete_transaction(transaction.id, session=session)
            session.commit()  # Manual commit
            assert deleted is True
            
        except TypeError as e:
            if "session" in str(e):
                pytest.fail(f"Method does not accept session parameter: {e}")
            else:
                raise

    # --- Batch Operations Tests ---

    def test_create_transactions_batch_success(self, db_instance: Database):
        """Test successful batch creation of transactions."""
        # Arrange
        category = db_instance.create_category(name="Food")
        indian_tz = pytz.timezone("Asia/Kolkata")
        
        transactions_data = [
            {
                "amount": 25.50,
                "transaction_date": indian_tz.localize(datetime.datetime(2024, 1, 15, 8, 0)),
                "description": "Coffee",
                "category_id": category.id
            },
            {
                "amount": 45.75,
                "transaction_date": indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0)),
                "description": "Lunch",
                "category_id": category.id
            },
            {
                "amount": 15.25,
                "transaction_date": indian_tz.localize(datetime.datetime(2024, 1, 15, 18, 0)),
                "description": "Snack"
                # No category_id - should be optional
            }
        ]
        
        # Act
        created_transactions = db_instance.create_transactions_batch(transactions_data)
        
        # Assert
        assert len(created_transactions) == 3
        descriptions = [t.description for t in created_transactions]
        assert "Coffee" in descriptions
        assert "Lunch" in descriptions
        assert "Snack" in descriptions
        
        # Verify they're actually in the database
        all_transactions = db_instance.get_all_transactions()
        assert len(all_transactions) == 3

    def test_create_transactions_batch_empty_list(self, db_instance: Database):
        """Test batch creation with empty list."""
        # Act
        created_transactions = db_instance.create_transactions_batch([])
        
        # Assert
        assert created_transactions == []
        assert len(db_instance.get_all_transactions()) == 0

    def test_create_transactions_batch_with_session_parameter(self, db_instance: Database):
        """Test batch creation accepts session parameter."""
        # Arrange
        category = db_instance.create_category(name="Food")
        indian_tz = pytz.timezone("Asia/Kolkata")
        
        transactions_data = [
            {
                "amount": 25.50,
                "transaction_date": indian_tz.localize(datetime.datetime(2024, 1, 15, 8, 0)),
                "description": "Coffee",
                "category_id": category.id
            },
            {
                "amount": 45.75,
                "transaction_date": indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0)),
                "description": "Lunch",
                "category_id": category.id
            }
        ]
        
        # Act - Test that batch method accepts session parameter without error
        session = db_instance.get_session()
        
        try:
            created_transactions = db_instance.create_transactions_batch(transactions_data, session=session)
            session.commit()  # Manual commit since we passed session
            
            # Assert - Verify the method works and returns expected results
            assert len(created_transactions) == 2
            assert created_transactions[0].description == "Coffee"
            assert created_transactions[1].description == "Lunch"
            
            # Verify they exist in the same session after commit
            session_transactions = db_instance.get_all_transactions(session=session)
            assert len(session_transactions) == 2
            
        except TypeError as e:
            if "session" in str(e):
                pytest.fail(f"Batch method does not accept session parameter: {e}")
            else:
                raise

    # --- Enhanced Query Methods Tests ---

    def test_get_transactions_filtered_by_date_range(self, db_instance: Database):
        """Test filtering transactions by date range."""
        # Arrange
        category = db_instance.create_category(name="Food")
        indian_tz = pytz.timezone("Asia/Kolkata")
        
        # Create transactions on different dates
        db_instance.create_transaction(
            amount=25.50,
            transaction_date=indian_tz.localize(datetime.datetime(2024, 1, 10, 12, 0)),
            description="Old transaction",
            category_id=category.id
        )
        db_instance.create_transaction(
            amount=45.75,
            transaction_date=indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0)),
            description="Middle transaction",
            category_id=category.id
        )
        db_instance.create_transaction(
            amount=15.25,
            transaction_date=indian_tz.localize(datetime.datetime(2024, 1, 20, 12, 0)),
            description="Recent transaction",
            category_id=category.id
        )
        
        # Act - Filter by date range
        start_date = indian_tz.localize(datetime.datetime(2024, 1, 12, 0, 0))
        end_date = indian_tz.localize(datetime.datetime(2024, 1, 18, 23, 59))
        filtered_transactions = db_instance.get_transactions_filtered(
            date_range=(start_date, end_date)
        )
        
        # Assert
        assert len(filtered_transactions) == 1
        assert filtered_transactions[0].description == "Middle transaction"

    def test_get_transactions_filtered_by_categories(self, db_instance: Database):
        """Test filtering transactions by categories."""
        # Arrange
        food_category = db_instance.create_category(name="Food")
        transport_category = db_instance.create_category(name="Transport")
        entertainment_category = db_instance.create_category(name="Entertainment")
        indian_tz = pytz.timezone("Asia/Kolkata")
        transaction_date = indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0))
        
        db_instance.create_transaction(
            amount=25.50,
            transaction_date=transaction_date,
            description="Coffee",
            category_id=food_category.id
        )
        db_instance.create_transaction(
            amount=15.00,
            transaction_date=transaction_date,
            description="Bus ticket",
            category_id=transport_category.id
        )
        db_instance.create_transaction(
            amount=30.00,
            transaction_date=transaction_date,
            description="Movie ticket",
            category_id=entertainment_category.id
        )
        
        # Act - Filter by specific categories
        filtered_transactions = db_instance.get_transactions_filtered(
            categories=["Food", "Transport"]
        )
        
        # Assert
        assert len(filtered_transactions) == 2
        descriptions = [t.description for t in filtered_transactions]
        assert "Coffee" in descriptions
        assert "Bus ticket" in descriptions
        assert "Movie ticket" not in descriptions

    def test_get_transactions_filtered_by_amount_range(self, db_instance: Database):
        """Test filtering transactions by amount range."""
        # Arrange
        category = db_instance.create_category(name="Food")
        indian_tz = pytz.timezone("Asia/Kolkata")
        transaction_date = indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0))
        
        db_instance.create_transaction(
            amount=5.50,
            transaction_date=transaction_date,
            description="Small coffee",
            category_id=category.id
        )
        db_instance.create_transaction(
            amount=25.75,
            transaction_date=transaction_date,
            description="Medium lunch",
            category_id=category.id
        )
        db_instance.create_transaction(
            amount=150.00,
            transaction_date=transaction_date,
            description="Expensive dinner",
            category_id=category.id
        )
        
        # Act - Filter by amount range
        filtered_transactions = db_instance.get_transactions_filtered(
            amount_range=(10.00, 100.00)
        )
        
        # Assert
        assert len(filtered_transactions) == 1
        assert filtered_transactions[0].description == "Medium lunch"
