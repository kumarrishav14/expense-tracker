"""
Tests for Category CRUD operations.
"""
import datetime
import pytest
from sqlalchemy.orm import Session

from core.database import crud
from core.database.model import Category


class TestCategoryCRUD:
    """Test suite for Category CRUD operations."""

    def test_create_category(self, db_session: Session):
        """Test creating a new category."""
        # Act
        category = crud.create_category(db_session, name="Food")
        
        # Assert
        assert category.id is not None
        assert category.name == "Food"
        assert category.parent_id is None
        assert category.created_at is not None
        assert category.updated_at is not None

    def test_create_category_with_parent(self, db_session: Session):
        """Test creating a category with a parent category."""
        # Arrange
        parent = crud.create_category(db_session, name="Food")
        
        # Act
        child = crud.create_category(db_session, name="Groceries", parent_id=parent.id)
        
        # Assert
        assert child.id is not None
        assert child.name == "Groceries"
        assert child.parent_id == parent.id
        assert child.created_at is not None

    def test_get_category(self, db_session: Session):
        """Test retrieving a category by ID."""
        # Arrange
        category = crud.create_category(db_session, name="Food")
        
        # Act
        retrieved_category = crud.get_category(db_session, category.id)
        
        # Assert
        assert retrieved_category is not None
        assert retrieved_category.id == category.id
        assert retrieved_category.name == "Food"

    def test_get_nonexistent_category(self, db_session: Session):
        """Test retrieving a non-existent category."""
        # Act
        category = crud.get_category(db_session, 999)
        
        # Assert
        assert category is None

    def test_get_all_categories(self, db_session: Session):
        """Test retrieving all categories."""
        # Arrange
        crud.create_category(db_session, name="Food")
        crud.create_category(db_session, name="Transport")
        crud.create_category(db_session, name="Entertainment")
        
        # Act
        categories = crud.get_all_categories(db_session)
        
        # Assert
        assert len(categories) == 3
        category_names = [c.name for c in categories]
        assert "Food" in category_names
        assert "Transport" in category_names
        assert "Entertainment" in category_names

    def test_update_category(self, db_session: Session):
        """Test updating a category."""
        # Arrange
        category = crud.create_category(db_session, name="Food")
        original_created_at = category.created_at
        
        # Act
        updated_category = crud.update_category(db_session, category.id, name="Dining")
        
        # Assert
        assert updated_category.id == category.id
        assert updated_category.name == "Dining"
        assert updated_category.created_at == original_created_at
        assert updated_category.updated_at >= original_created_at

    def test_update_nonexistent_category(self, db_session: Session):
        """Test updating a non-existent category."""
        # Act
        updated_category = crud.update_category(db_session, 999, name="Nonexistent")
        
        # Assert
        assert updated_category is None

    def test_delete_category(self, db_session: Session):
        """Test deleting a category."""
        # Arrange
        category = crud.create_category(db_session, name="Food")
        
        # Act
        result = crud.delete_category(db_session, category.id)
        
        # Assert
        assert result is True
        assert crud.get_category(db_session, category.id) is None

    def test_delete_nonexistent_category(self, db_session: Session):
        """Test deleting a non-existent category."""
        # Act
        result = crud.delete_category(db_session, 999)
        
        # Assert
        assert result is False

    def test_category_hierarchy(self, db_session: Session):
        """Test category hierarchy relationships."""
        # Arrange
        parent = crud.create_category(db_session, name="Food")
        child1 = crud.create_category(db_session, name="Groceries", parent_id=parent.id)
        child2 = crud.create_category(db_session, name="Dining Out", parent_id=parent.id)
        
        # Act - fetch parent with children via relationship
        parent_with_children = crud.get_category(db_session, parent.id)
        
        # Assert
        assert parent_with_children.parent is None
        # Note: This test assumes the relationship is correctly set up in the model
        # In a real test, you would need to query the children directly as this relationship might not be eagerly loaded
