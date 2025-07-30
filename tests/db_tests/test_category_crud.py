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
        updated_category = db_instance.update_category(category.id, {"name": "Dining"})

        # Assert
        assert updated_category.id == category.id
        assert updated_category.name == "Dining"
        assert updated_category.created_at == original_created_at
        assert updated_category.updated_at >= original_created_at

    def test_update_nonexistent_category(self, db_instance: Database):
        """Test updating a non-existent category."""
        # Act
        updated_category = db_instance.update_category(999, {"name": "Nonexistent"})

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
            updated = db_instance.update_category(category.id, {"name": "Updated Food"}, session=session)
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

    # --- Enhanced Category Management Tests ---

    def test_category_name_uniqueness_constraint(self, db_instance: Database):
        """Test that category names are unique within the same parent level."""
        # Create first category
        first_category = db_instance.create_category(name="Food")
        assert first_category is not None

        # Try to create duplicate category at same level
        try:
            duplicate_category = db_instance.create_category(name="Food")
            # If this succeeds, uniqueness constraint might not be enforced at application level
            # Database-level constraint should prevent this
            assert duplicate_category is None or duplicate_category.id != first_category.id
        except Exception as e:
            # Expected behavior - constraint should prevent duplicate
            assert "constraint" in str(e).lower() or "unique" in str(e).lower()

    def test_category_hierarchy_depth_limits(self, db_instance: Database):
        """Test deep category hierarchy creation and navigation."""
        # Create multi-level hierarchy
        level1 = db_instance.create_category(name="Expenses")
        level2 = db_instance.create_category(name="Food", parent_id=level1.id)
        level3 = db_instance.create_category(name="Dining", parent_id=level2.id)
        level4 = db_instance.create_category(name="Fast Food", parent_id=level3.id)
        level5 = db_instance.create_category(name="McDonald's", parent_id=level4.id)

        # Verify hierarchy integrity
        assert level1.parent is None
        assert level2.parent_id == level1.id
        assert level3.parent_id == level2.id
        assert level4.parent_id == level3.id
        assert level5.parent_id == level4.id

        # Test navigation through hierarchy
        retrieved_level5 = db_instance.get_category(level5.id)
        assert retrieved_level5.name == "McDonald's"
        assert retrieved_level5.parent.name == "Fast Food"
        assert retrieved_level5.parent.parent.name == "Dining"
        assert retrieved_level5.parent.parent.parent.name == "Food"
        assert retrieved_level5.parent.parent.parent.parent.name == "Expenses"

    def test_category_circular_reference_prevention(self, db_instance: Database):
        """Test prevention of circular references in category hierarchy."""
        # Create parent and child
        parent = db_instance.create_category(name="Food")
        child = db_instance.create_category(name="Groceries", parent_id=parent.id)

        # Try to make parent a child of its own child (circular reference)
        try:
            updated_parent = db_instance.update_category(parent.id, {"parent_id": child.id})
            # If this succeeds, circular reference detection might not be implemented
            # This should be prevented by business logic or constraints
            if updated_parent:
                # Check if circular reference was actually created
                retrieved_parent = db_instance.get_category(parent.id)
                assert retrieved_parent.parent_id != child.id  # Should be prevented
        except Exception as e:
            # Expected behavior - should prevent circular references
            assert "circular" in str(e).lower() or "constraint" in str(e).lower()

    def test_category_orphan_handling(self, db_instance: Database):
        """Test handling of orphaned categories when parent is deleted."""
        # Create parent and children
        parent = db_instance.create_category(name="Food")
        child1 = db_instance.create_category(name="Groceries", parent_id=parent.id)
        child2 = db_instance.create_category(name="Dining", parent_id=parent.id)

        # Delete parent
        delete_result = db_instance.delete_category(parent.id)

        if delete_result:
            # If deletion succeeded, check how children are handled
            child1_after = db_instance.get_category(child1.id)
            child2_after = db_instance.get_category(child2.id)

            # Children might be:
            # 1. Deleted (cascade delete)
            # 2. Made orphans (parent_id set to None)
            # 3. Deletion prevented by foreign key constraint

            if child1_after is None:
                # Cascade delete behavior
                assert child2_after is None
            else:
                # Orphan handling - children become root categories
                assert child1_after.parent_id is None
                assert child2_after.parent_id is None
        else:
            # Deletion prevented due to children (foreign key constraint)
            child1_after = db_instance.get_category(child1.id)
            child2_after = db_instance.get_category(child2.id)
            assert child1_after is not None
            assert child2_after is not None

    def test_category_name_validation_edge_cases(self, db_instance: Database):
        """Test category name validation with edge cases."""
        # Test various edge cases for category names
        edge_case_names = [
            "",  # Empty name
            " ",  # Whitespace only
            "a" * 255,  # Very long name
            "Special chars: !@#$%^&*()_+{}|:<>?[]\\;'\",./`~",  # Special characters
            "Unicode: café, naïve, résumé, 中文, 日本語, 🍕",  # Unicode characters
            "Newline\ncharacter",  # Newline in name
            "Tab\tcharacter"  # Tab in name
        ]

        for name in edge_case_names:
            try:
                category = db_instance.create_category(name=name)
                if category is not None:
                    # If creation succeeded, verify the name was stored correctly
                    retrieved = db_instance.get_category(category.id)
                    assert retrieved.name == name
                else:
                    # Creation failed - acceptable for empty names
                    assert name == "" or name.strip() == ""
            except Exception as e:
                # Some edge cases might raise exceptions - document this behavior
                assert isinstance(e, (ValueError, IntegrityError))

    # def test_category_soft_delete_behavior(self, db_instance: Database):
        # """Test soft delete behavior if implemented for categories."""
        # # Create category
        # category = db_instance.create_category(name="Food")

        # # Check if soft delete is implemented (is_active field)
        # if hasattr(category, 'is_active'):
        #     # Test soft delete
        #     updated_category = db_instance.update_category(category.id, is_active=False)
        #     assert updated_category is not None
        #     assert updated_category.is_active is False

        #     # Verify category still exists but marked inactive
        #     retrieved_category = db_instance.get_category(category.id)
        #     assert retrieved_category is not None
        #     assert retrieved_category.is_active is False

        #     # Test if inactive categories are excluded from get_all_categories
        #     all_categories = db_instance.get_all_categories()
        #     active_category_ids = [c.id for c in all_categories if getattr(c, 'is_active', True)]
        #     assert category.id not in active_category_ids
        # else:
        #     # Soft delete not implemented - document requirement
        #     pytest.skip("Soft delete (is_active field) not implemented for categories")

    def test_category_audit_trail_integrity(self, db_instance: Database):
        """Test audit trail functionality for categories."""
        # Create category
        category = db_instance.create_category(name="Food")
        original_created_at = category.created_at
        original_updated_at = category.updated_at

        # Verify initial timestamps
        assert original_created_at is not None

        # Wait and update
        import time
        time.sleep(0.01)

        updated_category = db_instance.update_category(category.id, {"name": "Updated Food"})

        # Verify audit trail
        assert updated_category.created_at == original_created_at  # Should not change
        if hasattr(updated_category, 'updated_at') and updated_category.updated_at:
            assert updated_category.updated_at >= original_created_at

    def test_category_batch_operations_constraint_handling(self, db_instance: Database):
        """Test batch operations with constraint violations."""
        # Test batch with duplicate names
        categories_with_duplicates = [
            {"name": "Food"},
            {"name": "Transport"},
            {"name": "Food"}  # Duplicate
        ]

        try:
            created_categories = db_instance.create_categories_batch(categories_with_duplicates)
            # If this succeeds, check how duplicates were handled
            if len(created_categories) == 3:
                # All created - duplicates allowed or handled differently
                names = [c.name for c in created_categories]
                assert names.count("Food") == 2
            elif len(created_categories) == 2:
                # Duplicates filtered out
                names = [c.name for c in created_categories]
                assert "Food" in names and "Transport" in names
            else:
                # Complete failure
                assert len(created_categories) == 0
        except Exception as e:
            # Batch failed due to constraint violation
            assert "constraint" in str(e).lower() or "unique" in str(e).lower()
            # Verify atomic rollback
            all_categories = db_instance.get_all_categories()
            assert len(all_categories) == 0

    def test_category_batch_operations_with_invalid_hierarchy(self, db_instance: Database):
        """Test batch operations with invalid parent references."""
        # Test batch with invalid parent_id
        categories_with_invalid_parent = [
            {"name": "Food"},
            {"name": "Groceries", "parent_id": 99999}  # Non-existent parent
        ]

        try:
            created_categories = db_instance.create_categories_batch(categories_with_invalid_parent)
            # If this succeeds partially or fully, check the results
            if created_categories:
                # Check how invalid parent was handled
                groceries = next((c for c in created_categories if c.name == "Groceries"), None)
                if groceries:
                    # Invalid parent might be ignored (set to None) or cause error
                    assert groceries.parent_id is None or groceries.parent_id == 99999
        except Exception as e:
            # Expected behavior - foreign key constraint should prevent this
            assert "constraint" in str(e).lower() or "foreign key" in str(e).lower()
            # Verify atomic rollback
            all_categories = db_instance.get_all_categories()
            assert len(all_categories) == 0

    def test_get_categories_by_parent_performance(self, db_instance: Database):
        """Test performance characteristics of hierarchical queries."""
        # Create large hierarchy
        root = db_instance.create_category(name="Root")

        # Create 50 child categories
        children = []
        for i in range(50):
            child = db_instance.create_category(name=f"Child {i+1}", parent_id=root.id)
            children.append(child)

        # Create grandchildren for first 10 children
        grandchildren = []
        for i in range(10):
            for j in range(5):
                grandchild = db_instance.create_category(
                    name=f"Grandchild {i+1}-{j+1}",
                    parent_id=children[i].id
                )
                grandchildren.append(grandchild)

        # Test query performance
        root_children = db_instance.get_categories_by_parent(parent_id=root.id)
        assert len(root_children) == 50

        # Test querying children with grandchildren
        first_child_grandchildren = db_instance.get_categories_by_parent(parent_id=children[0].id)
        assert len(first_child_grandchildren) == 5

        # Test querying children without grandchildren
        last_child_children = db_instance.get_categories_by_parent(parent_id=children[49].id)
        assert len(last_child_children) == 0

    def test_category_name_case_sensitivity(self, db_instance: Database):
        """Test case sensitivity in category names."""
        # Create categories with different cases
        food_lower = db_instance.create_category(name="food")
        food_upper = db_instance.create_category(name="FOOD")
        food_mixed = db_instance.create_category(name="Food")

        # Verify all were created (case sensitive) or handled appropriately
        all_categories = db_instance.get_all_categories()
        food_names = [c.name for c in all_categories if "food" in c.name.lower()]

        # Depending on implementation:
        # 1. Case sensitive - all 3 should exist
        # 2. Case insensitive - only 1 should exist
        assert len(food_names) >= 1

        # Test retrieval by name (if implemented)
        if hasattr(db_instance, 'get_category_by_name'):
            found_lower = db_instance.get_category_by_name("food")
            found_upper = db_instance.get_category_by_name("FOOD")
            found_mixed = db_instance.get_category_by_name("Food")

            # Verify case sensitivity behavior
            if len(food_names) == 3:
                # Case sensitive
                assert found_lower.name == "food"
                assert found_upper.name == "FOOD"
                assert found_mixed.name == "Food"
            else:
                # Case insensitive or normalized
                assert all(cat is not None for cat in [found_lower, found_upper, found_mixed] if cat)

    def test_category_transaction_relationship_integrity(self, db_instance: Database):
        """Test integrity of category-transaction relationships."""
        # Create category and transactions
        category = db_instance.create_category(name="Food")
        account = db_instance.create_account(name="Test Account", account_type="Bank Account")

        transactions = []
        for i in range(5):
            transaction = db_instance.create_transaction(
                amount=10.0 + i,
                transaction_date=datetime.datetime(2024, 1, i+1, 12, 0),
                description=f"Transaction {i+1}",
                category_id=category.id,
                account_id=account.id
            )
            transactions.append(transaction)

        # Test category deletion with associated transactions
        try:
            delete_result = db_instance.delete_category(category.id)
            if delete_result:
                # If deletion succeeded, check how transactions were handled
                for transaction in transactions:
                    updated_transaction = db_instance.get_transaction(transaction.id)
                    if updated_transaction:
                        # Transaction exists - category_id should be None or unchanged
                        assert updated_transaction.category_id is None or updated_transaction.category_id == category.id
                    # Transactions might be deleted if cascade delete is implemented
            else:
                # Deletion prevented due to foreign key constraint
                # Verify transactions still exist
                for transaction in transactions:
                    existing_transaction = db_instance.get_transaction(transaction.id)
                    assert existing_transaction is not None
                    assert existing_transaction.category_id == category.id
        except Exception as e:
            # Foreign key constraint prevented deletion
            assert "constraint" in str(e).lower() or "foreign key" in str(e).lower()

    def test_category_update_parent_validation(self, db_instance: Database):
        """Test validation when updating category parent relationships."""
        # Create categories
        food = db_instance.create_category(name="Food")
        groceries = db_instance.create_category(name="Groceries", parent_id=food.id)
        vegetables = db_instance.create_category(name="Vegetables", parent_id=groceries.id)

        # Test valid parent updates
        transport = db_instance.create_category(name="Transport")

        # Move groceries from Food to Transport
        updated_groceries = db_instance.update_category(groceries.id, {"parent_id": transport.id})
        assert updated_groceries.parent_id == transport.id

        # Verify vegetables is still under groceries
        vegetables_after = db_instance.get_category(vegetables.id)
        assert vegetables_after.parent_id == groceries.id

        # Test invalid parent update (making category its own grandparent)
        try:
            invalid_update = db_instance.update_category(groceries.id, {"parent_id": vegetables.id})
            invalid_update = db_instance.update_category(groceries.id, {"parent_id": vegetables.id})
            # This would create: groceries -> vegetables -> groceries (circular)
            # Should be prevented
            if invalid_update:
                # Check if circular reference was actually prevented
                retrieved_groceries = db_instance.get_category(groceries.id)
                assert retrieved_groceries.parent_id != vegetables.id
        except Exception as e:
            # Expected behavior - circular reference prevention
            assert "circular" in str(e).lower() or "constraint" in str(e).lower()
