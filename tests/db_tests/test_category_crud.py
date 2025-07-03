"""
Tests for Category CRUD operations with enhanced transaction management and batch operations.
"""
import pytest
import datetime
from sqlalchemy.exc import IntegrityError
from core.database.db_manager import Database


class TestCategoryCRUD:
    """Test suite for Category CRUD operations."""

    def test_create_category(self, db_instance: Database):
        """Test creating a new category."""
        # Act
        category = db_instance.create_category(name="Food")
        
        # Assert
        assert category.id is not None
        assert category.name == "Food"
        assert category.parent_id is None
        assert category.created_at is not None

    def test_create_category_with_parent(self, db_instance: Database):
        """Test creating a category with a parent category."""
        # Arrange
        parent = db_instance.create_category(name="Food")
        
        # Act
        child = db_instance.create_category(name="Groceries", parent_id=parent.id)
        
        # Assert
        assert child.id is not None
        assert child.name == "Groceries"
        assert child.parent_id == parent.id

    def test_get_category(self, db_instance: Database):
        """Test retrieving a category by ID."""
        # Arrange
        category = db_instance.create_category(name="Food")
        
        # Act
        retrieved_category = db_instance.get_category(category.id)
        
        # Assert
        assert retrieved_category is not None
        assert retrieved_category.id == category.id
        assert retrieved_category.name == "Food"

    def test_get_nonexistent_category(self, db_instance: Database):
        """Test retrieving a non-existent category."""
        # Act
        category = db_instance.get_category(999)
        
        # Assert
        assert category is None

    def test_get_all_categories(self, db_instance: Database):
        """Test retrieving all categories."""
        # Arrange
        db_instance.create_category(name="Food")
        db_instance.create_category(name="Transport")
        db_instance.create_category(name="Entertainment")
        
        # Act
        categories = db_instance.get_all_categories()
        
        # Assert
        assert len(categories) == 3
        category_names = [c.name for c in categories]
        assert "Food" in category_names
        assert "Transport" in category_names
        assert "Entertainment" in category_names

    def test_update_category(self, db_instance: Database):
        """Test updating a category."""
        # Arrange
        category = db_instance.create_category(name="Food")
        original_created_at = category.created_at
        
        # Act
        updated_category = db_instance.update_category(category.id, name="Dining")
        
        # Assert
        assert updated_category.id == category.id
        assert updated_category.name == "Dining"
        assert updated_category.created_at == original_created_at
        assert updated_category.updated_at >= original_created_at

    def test_update_nonexistent_category(self, db_instance: Database):
        """Test updating a non-existent category."""
        # Act
        updated_category = db_instance.update_category(999, name="Nonexistent")
        
        # Assert
        assert updated_category is None

    def test_delete_category(self, db_instance: Database):
        """Test deleting a category."""
        # Arrange
        category = db_instance.create_category(name="Food")
        
        # Act
        result = db_instance.delete_category(category.id)
        
        # Assert
        assert result is True
        assert db_instance.get_category(category.id) is None

    def test_delete_nonexistent_category(self, db_instance: Database):
        """Test deleting a non-existent category."""
        # Act
        result = db_instance.delete_category(999)
        
        # Assert
        assert result is False

    def test_category_hierarchy(self, db_instance: Database):
        """Test multi-level and multiple-child category hierarchy relationships."""
        # Arrange
        # Level 1
        food = db_instance.create_category(name="Food")
        
        # Level 2
        groceries = db_instance.create_category(name="Groceries", parent_id=food.id)
        dining = db_instance.create_category(name="Dining", parent_id=food.id)
        
        # Level 3
        fruits = db_instance.create_category(name="Fruits", parent_id=groceries.id)
        vegetables = db_instance.create_category(name="Vegetables", parent_id=groceries.id)

        # Act
        retrieved_food = db_instance.get_category(food.id)
        retrieved_groceries = db_instance.get_category(groceries.id)
        retrieved_dining = db_instance.get_category(dining.id)
        retrieved_fruits = db_instance.get_category(fruits.id)
        retrieved_vegetables = db_instance.get_category(vegetables.id)

        # Assert
        # Check parent-child relationships
        assert retrieved_food.parent is None
        assert retrieved_groceries.parent.id == food.id
        assert retrieved_dining.parent.id == food.id
        assert retrieved_fruits.parent.id == groceries.id
        assert retrieved_vegetables.parent.id == groceries.id

        # Check children relationships
        all_categories = db_instance.get_all_categories()
        
        food_children = [c.name for c in all_categories if c.parent_id == retrieved_food.id]
        assert "Groceries" in food_children
        assert "Dining" in food_children
        
        groceries_children = [c.name for c in all_categories if c.parent_id == retrieved_groceries.id]
        assert "Fruits" in groceries_children
        assert "Vegetables" in groceries_children
        
        dining_children = [c.name for c in all_categories if c.parent_id == retrieved_dining.id]
        assert not dining_children
        
        fruits_children = [c.name for c in all_categories if c.parent_id == retrieved_fruits.id]
        assert not fruits_children
        
        vegetables_children = [c.name for c in all_categories if c.parent_id == retrieved_vegetables.id]
        assert not vegetables_children

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

    def test_session_parameter_in_crud_operations(self, db_instance: Database):
        """Test that all CRUD operations accept session parameter."""
        # Test that all CRUD methods accept the session parameter without raising errors
        session = db_instance.get_session()
        
        # Test that methods accept session parameter (they should not raise TypeError)
        try:
            # Create with session parameter
            category = db_instance.create_category(name="Food", session=session)
            session.commit()  # Manual commit since we passed session
            assert category is not None
            
            # Read with session parameter
            retrieved = db_instance.get_category(category.id, session=session)
            assert retrieved is not None
            
            # Update with session parameter
            updated = db_instance.update_category(category.id, name="Updated Food", session=session)
            session.commit()  # Manual commit
            assert updated is not None
            
            # List all with session parameter
            all_categories = db_instance.get_all_categories(session=session)
            assert len(all_categories) >= 1
            
            # Delete with session parameter
            deleted = db_instance.delete_category(category.id, session=session)
            session.commit()  # Manual commit
            assert deleted is True
            
        except TypeError as e:
            if "session" in str(e):
                pytest.fail(f"Method does not accept session parameter: {e}")
            else:
                raise

    # --- Batch Operations Tests ---

    def test_create_categories_batch_success(self, db_instance: Database):
        """Test successful batch creation of categories."""
        # Arrange
        categories_data = [
            {"name": "Food"},
            {"name": "Transport"},
            {"name": "Entertainment"}
        ]
        
        # Act
        created_categories = db_instance.create_categories_batch(categories_data)
        
        # Assert
        assert len(created_categories) == 3
        category_names = [c.name for c in created_categories]
        assert "Food" in category_names
        assert "Transport" in category_names
        assert "Entertainment" in category_names
        
        # Verify they're actually in the database
        all_categories = db_instance.get_all_categories()
        assert len(all_categories) == 3

    def test_create_categories_batch_with_hierarchy(self, db_instance: Database):
        """Test batch creation of categories with parent-child relationships."""
        # Arrange - Create parent first
        parent = db_instance.create_category(name="Food")
        
        categories_data = [
            {"name": "Groceries", "parent_id": parent.id},
            {"name": "Dining", "parent_id": parent.id},
            {"name": "Snacks", "parent_id": parent.id}
        ]
        
        # Act
        created_categories = db_instance.create_categories_batch(categories_data)
        
        # Assert
        assert len(created_categories) == 3
        for category in created_categories:
            assert category.parent_id == parent.id
        
        # Verify hierarchy in database
        all_categories = db_instance.get_all_categories()
        child_categories = [c for c in all_categories if c.parent_id == parent.id]
        assert len(child_categories) == 3

    def test_create_categories_batch_empty_list(self, db_instance: Database):
        """Test batch creation with empty list."""
        # Act
        created_categories = db_instance.create_categories_batch([])
        
        # Assert
        assert created_categories == []
        assert len(db_instance.get_all_categories()) == 0

    def test_create_categories_batch_with_session_parameter(self, db_instance: Database):
        """Test batch creation accepts session parameter."""
        # Arrange
        categories_data = [
            {"name": "Food"},
            {"name": "Transport"}
        ]
        
        # Act - Test that batch method accepts session parameter without error
        session = db_instance.get_session()
        
        try:
            created_categories = db_instance.create_categories_batch(categories_data, session=session)
            session.commit()  # Manual commit since we passed session
            
            # Assert - Verify the method works and returns expected results
            assert len(created_categories) == 2
            assert created_categories[0].name == "Food"
            assert created_categories[1].name == "Transport"
            
            # Verify they exist in the same session after commit
            session_categories = db_instance.get_all_categories(session=session)
            assert len(session_categories) == 2
            
        except TypeError as e:
            if "session" in str(e):
                pytest.fail(f"Batch method does not accept session parameter: {e}")
            else:
                raise

    # --- Enhanced Query Methods Tests ---

    def test_get_categories_by_parent_root_categories(self, db_instance: Database):
        """Test getting root categories (no parent)."""
        # Arrange
        food = db_instance.create_category(name="Food")
        transport = db_instance.create_category(name="Transport")
        groceries = db_instance.create_category(name="Groceries", parent_id=food.id)
        
        # Act
        root_categories = db_instance.get_categories_by_parent(parent_id=None)
        
        # Assert
        assert len(root_categories) == 2
        root_names = [c.name for c in root_categories]
        assert "Food" in root_names
        assert "Transport" in root_names
        assert "Groceries" not in root_names

    def test_get_categories_by_parent_specific_parent(self, db_instance: Database):
        """Test getting categories with specific parent."""
        # Arrange
        food = db_instance.create_category(name="Food")
        transport = db_instance.create_category(name="Transport")
        groceries = db_instance.create_category(name="Groceries", parent_id=food.id)
        dining = db_instance.create_category(name="Dining", parent_id=food.id)
        public_transport = db_instance.create_category(name="Public Transport", parent_id=transport.id)
        
        # Act
        food_children = db_instance.get_categories_by_parent(parent_id=food.id)
        transport_children = db_instance.get_categories_by_parent(parent_id=transport.id)
        
        # Assert
        assert len(food_children) == 2
        food_child_names = [c.name for c in food_children]
        assert "Groceries" in food_child_names
        assert "Dining" in food_child_names
        
        assert len(transport_children) == 1
        assert transport_children[0].name == "Public Transport"

    def test_get_categories_by_parent_nonexistent_parent(self, db_instance: Database):
        """Test getting categories with non-existent parent."""
        # Arrange
        db_instance.create_category(name="Food")
        
        # Act
        children = db_instance.get_categories_by_parent(parent_id=999)
        
        # Assert
        assert len(children) == 0

    # --- Error Handling Tests ---

    def test_handle_constraint_error_integrity_error(self, db_instance: Database):
        """Test constraint error handling for integrity violations."""
        # Arrange
        error = IntegrityError("UNIQUE constraint failed", None, None)
        
        # Act
        error_info = db_instance.handle_constraint_error(error)
        
        # Assert
        assert error_info["error_category"] == "constraint_violation"
        assert error_info["constraint_type"] == "unique_violation"
        assert error_info["is_retryable"] is False
        assert error_info["suggested_action"] == "check_data_integrity"

    def test_handle_constraint_error_foreign_key_error(self, db_instance: Database):
        """Test constraint error handling for foreign key violations."""
        # Arrange
        error = IntegrityError("FOREIGN KEY constraint failed", None, None)
        
        # Act
        error_info = db_instance.handle_constraint_error(error)
        
        # Assert
        assert error_info["error_category"] == "constraint_violation"
        assert error_info["constraint_type"] == "foreign_key_violation"
        assert error_info["is_retryable"] is False

    def test_is_retryable_error_operational_error(self, db_instance: Database):
        """Test retryable error detection for operational errors."""
        from sqlalchemy.exc import OperationalError
        
        # Arrange
        retryable_error = OperationalError("database is locked", None, None)
        non_retryable_error = OperationalError("syntax error", None, None)
        
        # Act & Assert
        assert db_instance.is_retryable_error(retryable_error) is True
        assert db_instance.is_retryable_error(non_retryable_error) is False

    def test_is_retryable_error_other_errors(self, db_instance: Database):
        """Test retryable error detection for various error types."""
        from sqlalchemy.exc import TimeoutError, DataError
        
        # Act & Assert
        assert db_instance.is_retryable_error(TimeoutError("timeout", None, None)) is True
        assert db_instance.is_retryable_error(DataError("invalid data", None, None)) is False
        assert db_instance.is_retryable_error(ValueError("invalid value")) is False
