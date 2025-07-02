"""
Tests for Category CRUD operations.
"""
import pytest
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
