"""
Tests for DatabaseInterface - the interface between pandas DataFrames and database tables.

This test suite validates the enhanced DatabaseInterface class which:
1. Acts as an interface between pandas tables and SQL operations with atomic transaction support
2. Separates frontend and other components from SQL infrastructure
3. Helps retrieve data from SQL tables with enhanced error handling
4. For transaction table, identifies relations and merges tables returning merged pandas table
5. Adds category and sub-category columns while merging tables
6. Helps save new data to SQL DB using atomic transactions and batch operations
7. Provides comprehensive error handling with constraint classification
8. Supports session-aware operations for better transaction management
"""
import pytest
import pandas as pd
import datetime
from decimal import Decimal
import pytz
from sqlalchemy.exc import IntegrityError, OperationalError

from core.database.db_interface import DatabaseInterface
from core.database.db_manager import Database


class TestDatabaseInterface:
    """Test suite for DatabaseInterface operations."""

    @pytest.fixture
    def db_interface(self, db_instance: Database, monkeypatch):
        """
        Provides a DatabaseInterface instance using the test database.
        """
        interface = DatabaseInterface(db_url="sqlite:///:memory:")
        # Monkeypatch to use the same test database instance
        monkeypatch.setattr(interface, "db", db_instance)
        return interface

    # --- Test Category Table Operations ---

    def test_get_categories_table_empty(self, db_interface: DatabaseInterface):
        """Test getting categories table when no categories exist."""
        # Act
        df = db_interface.get_categories_table()
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['name', 'parent_category']
        assert len(df) == 0

    def test_get_categories_table_simple_categories(self, db_interface: DatabaseInterface):
        """Test getting categories table with simple categories (no hierarchy)."""
        # Arrange
        db_interface.db.create_category(name="Food")
        db_interface.db.create_category(name="Transport")
        db_interface.db.create_category(name="Entertainment")
        
        # Act
        df = db_interface.get_categories_table()
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ['name', 'parent_category']
        assert len(df) == 3
        
        # Check all categories are present
        category_names = df['name'].tolist()
        assert "Food" in category_names
        assert "Transport" in category_names
        assert "Entertainment" in category_names
        
        # Check all parent_category values are None for simple categories
        assert df['parent_category'].isna().all()

    def test_get_categories_table_with_hierarchy(self, db_interface: DatabaseInterface):
        """Test getting categories table with parent-child hierarchy."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        groceries = db_interface.db.create_category(name="Groceries", parent_id=food.id)
        dining = db_interface.db.create_category(name="Dining", parent_id=food.id)
        
        transport = db_interface.db.create_category(name="Transport")
        public_transport = db_interface.db.create_category(name="Public Transport", parent_id=transport.id)
        
        # Act
        df = db_interface.get_categories_table()
        
        # Assert
        assert len(df) == 5
        
        # Check parent categories
        food_row = df[df['name'] == 'Food'].iloc[0]
        assert pd.isna(food_row['parent_category'])
        
        transport_row = df[df['name'] == 'Transport'].iloc[0]
        assert pd.isna(transport_row['parent_category'])
        
        # Check child categories
        groceries_row = df[df['name'] == 'Groceries'].iloc[0]
        assert groceries_row['parent_category'] == 'Food'
        
        dining_row = df[df['name'] == 'Dining'].iloc[0]
        assert dining_row['parent_category'] == 'Food'
        
        public_transport_row = df[df['name'] == 'Public Transport'].iloc[0]
        assert public_transport_row['parent_category'] == 'Transport'

    # --- Test Transaction Table Operations ---

    def test_get_transactions_table_empty(self, db_interface: DatabaseInterface):
        """Test getting transactions table when no transactions exist."""
        # Act
        df = db_interface.get_transactions_table()
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(df.columns) == expected_columns
        assert len(df) == 0

    def test_get_transactions_table_without_categories(self, db_interface: DatabaseInterface):
        """Test getting transactions table with transactions but no categories assigned."""
        # Arrange
        indian_tz = pytz.timezone("Asia/Kolkata")
        date1 = indian_tz.localize(datetime.datetime(2024, 1, 15, 10, 30))
        date2 = indian_tz.localize(datetime.datetime(2024, 1, 16, 14, 45))
        
        db_interface.db.create_transaction(
            amount=Decimal("25.50"),
            transaction_date=date1,
            description="Coffee shop"
        )
        db_interface.db.create_transaction(
            amount=Decimal("100.00"),
            transaction_date=date2,
            description="Grocery shopping"
        )
        
        # Act
        df = db_interface.get_transactions_table()
        
        # Assert
        assert len(df) == 2
        assert df['category'].eq("").all()
        assert df['sub_category'].eq("").all()
        
        # Check transaction data
        assert df['description'].tolist() == ["Coffee shop", "Grocery shopping"]
        assert df['amount'].tolist() == [25.50, 100.00]
        assert isinstance(df['transaction_date'].iloc[0], pd.Timestamp)

    def test_get_transactions_table_with_parent_categories_only(self, db_interface: DatabaseInterface):
        """Test transactions with categories that have no parent (top-level categories)."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        transport = db_interface.db.create_category(name="Transport")
        
        indian_tz = pytz.timezone("Asia/Kolkata")
        date1 = indian_tz.localize(datetime.datetime(2024, 1, 15, 10, 30))
        date2 = indian_tz.localize(datetime.datetime(2024, 1, 16, 14, 45))
        
        db_interface.db.create_transaction(
            amount=Decimal("25.50"),
            transaction_date=date1,
            description="Restaurant",
            category_id=food.id
        )
        db_interface.db.create_transaction(
            amount=Decimal("15.00"),
            transaction_date=date2,
            description="Bus ticket",
            category_id=transport.id
        )
        
        # Act
        df = db_interface.get_transactions_table()
        
        # Assert
        assert len(df) == 2
        
        # For top-level categories: category = category name, sub_category = ""
        restaurant_row = df[df['description'] == 'Restaurant'].iloc[0]
        assert restaurant_row['category'] == 'Food'
        assert restaurant_row['sub_category'] == ""
        
        bus_row = df[df['description'] == 'Bus ticket'].iloc[0]
        assert bus_row['category'] == 'Transport'
        assert bus_row['sub_category'] == ""

    def test_get_transactions_table_with_sub_categories(self, db_interface: DatabaseInterface):
        """Test transactions with sub-categories (categories that have parents)."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        groceries = db_interface.db.create_category(name="Groceries", parent_id=food.id)
        dining = db_interface.db.create_category(name="Dining", parent_id=food.id)
        
        transport = db_interface.db.create_category(name="Transport")
        public_transport = db_interface.db.create_category(name="Public Transport", parent_id=transport.id)
        
        indian_tz = pytz.timezone("Asia/Kolkata")
        date1 = indian_tz.localize(datetime.datetime(2024, 1, 15, 10, 30))
        date2 = indian_tz.localize(datetime.datetime(2024, 1, 16, 14, 45))
        date3 = indian_tz.localize(datetime.datetime(2024, 1, 17, 18, 20))
        
        db_interface.db.create_transaction(
            amount=Decimal("45.75"),
            transaction_date=date1,
            description="Supermarket",
            category_id=groceries.id
        )
        db_interface.db.create_transaction(
            amount=Decimal("28.50"),
            transaction_date=date2,
            description="Restaurant dinner",
            category_id=dining.id
        )
        db_interface.db.create_transaction(
            amount=Decimal("5.00"),
            transaction_date=date3,
            description="Metro ticket",
            category_id=public_transport.id
        )
        
        # Act
        df = db_interface.get_transactions_table()
        
        # Assert
        assert len(df) == 3
        
        # For sub-categories: category = parent name, sub_category = category name
        supermarket_row = df[df['description'] == 'Supermarket'].iloc[0]
        assert supermarket_row['category'] == 'Food'
        assert supermarket_row['sub_category'] == 'Groceries'
        
        restaurant_row = df[df['description'] == 'Restaurant dinner'].iloc[0]
        assert restaurant_row['category'] == 'Food'
        assert restaurant_row['sub_category'] == 'Dining'
        
        metro_row = df[df['description'] == 'Metro ticket'].iloc[0]
        assert metro_row['category'] == 'Transport'
        assert metro_row['sub_category'] == 'Public Transport'

    def test_get_transactions_table_mixed_categories(self, db_interface: DatabaseInterface):
        """Test transactions with mix of top-level categories and sub-categories."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        groceries = db_interface.db.create_category(name="Groceries", parent_id=food.id)
        entertainment = db_interface.db.create_category(name="Entertainment")  # Top-level
        
        indian_tz = pytz.timezone("Asia/Kolkata")
        date1 = indian_tz.localize(datetime.datetime(2024, 1, 15, 10, 30))
        date2 = indian_tz.localize(datetime.datetime(2024, 1, 16, 14, 45))
        date3 = indian_tz.localize(datetime.datetime(2024, 1, 17, 18, 20))
        
        # Transaction with sub-category
        db_interface.db.create_transaction(
            amount=Decimal("45.75"),
            transaction_date=date1,
            description="Weekly groceries",
            category_id=groceries.id
        )
        # Transaction with top-level category
        db_interface.db.create_transaction(
            amount=Decimal("15.00"),
            transaction_date=date2,
            description="Movie ticket",
            category_id=entertainment.id
        )
        # Transaction with no category
        db_interface.db.create_transaction(
            amount=Decimal("10.00"),
            transaction_date=date3,
            description="Unknown expense"
        )
        
        # Act
        df = db_interface.get_transactions_table()
        
        # Assert
        assert len(df) == 3
        
        groceries_row = df[df['description'] == 'Weekly groceries'].iloc[0]
        assert groceries_row['category'] == 'Food'
        assert groceries_row['sub_category'] == 'Groceries'
        
        movie_row = df[df['description'] == 'Movie ticket'].iloc[0]
        assert movie_row['category'] == 'Entertainment'
        assert movie_row['sub_category'] == ""
        
        unknown_row = df[df['description'] == 'Unknown expense'].iloc[0]
        assert unknown_row['category'] == ""
        assert unknown_row['sub_category'] == ""

    # --- Test Category Resolution Helper Methods ---

    def test_resolve_category_id_empty_category(self, db_interface: DatabaseInterface):
        """Test resolving category ID with empty category name."""
        # Act
        category_id = db_interface._resolve_category_id("", "")
        
        # Assert
        assert category_id is None

    def test_resolve_category_id_top_level_category(self, db_interface: DatabaseInterface):
        """Test resolving category ID for top-level category."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        
        # Act
        category_id = db_interface._resolve_category_id("Food", "")
        
        # Assert
        assert category_id == food.id

    def test_resolve_category_id_sub_category(self, db_interface: DatabaseInterface):
        """Test resolving category ID for sub-category."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        groceries = db_interface.db.create_category(name="Groceries", parent_id=food.id)
        
        # Act
        category_id = db_interface._resolve_category_id("Food", "Groceries")
        
        # Assert
        assert category_id == groceries.id

    def test_resolve_category_id_nonexistent_category(self, db_interface: DatabaseInterface):
        """Test resolving category ID for non-existent category."""
        # Act
        category_id = db_interface._resolve_category_id("NonExistent", "")
        
        # Assert
        assert category_id is None

    def test_resolve_category_id_nonexistent_sub_category(self, db_interface: DatabaseInterface):
        """Test resolving category ID for non-existent sub-category."""
        # Arrange
        db_interface.db.create_category(name="Food")
        
        # Act
        category_id = db_interface._resolve_category_id("Food", "NonExistent")
        
        # Assert
        assert category_id is None

    # --- Test Category Hierarchy Creation ---

    def test_create_category_hierarchy_empty_category(self, db_interface: DatabaseInterface):
        """Test creating category hierarchy with empty category name."""
        # Act
        result = db_interface.create_category_hierarchy("", "")
        
        # Assert
        assert result is False

    def test_create_category_hierarchy_top_level_only(self, db_interface: DatabaseInterface):
        """Test creating only top-level category."""
        # Act
        result = db_interface.create_category_hierarchy("Food", "")
        
        # Assert
        assert result is True
        
        # Verify category was created
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 1
        assert categories[0].name == "Food"
        assert categories[0].parent is None

    def test_create_category_hierarchy_with_sub_category(self, db_interface: DatabaseInterface):
        """Test creating category hierarchy with sub-category."""
        # Act
        result = db_interface.create_category_hierarchy("Food", "Groceries")
        
        # Assert
        assert result is True
        
        # Verify categories were created
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 2
        
        # Find parent and child
        parent = next(cat for cat in categories if cat.name == "Food")
        child = next(cat for cat in categories if cat.name == "Groceries")
        
        assert parent.parent is None
        assert child.parent_id == parent.id

    def test_create_category_hierarchy_existing_parent(self, db_interface: DatabaseInterface):
        """Test creating sub-category when parent already exists."""
        # Arrange
        existing_parent = db_interface.db.create_category(name="Food")
        
        # Act
        result = db_interface.create_category_hierarchy("Food", "Groceries")
        
        # Assert
        assert result is True
        
        # Verify only one new category was created
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 2
        
        # Verify the existing parent was used
        child = next(cat for cat in categories if cat.name == "Groceries")
        assert child.parent_id == existing_parent.id

    def test_create_category_hierarchy_existing_both(self, db_interface: DatabaseInterface):
        """Test creating hierarchy when both parent and child already exist."""
        # Arrange
        parent = db_interface.db.create_category(name="Food")
        child = db_interface.db.create_category(name="Groceries", parent_id=parent.id)
        
        # Act
        result = db_interface.create_category_hierarchy("Food", "Groceries")
        
        # Assert
        assert result is True
        
        # Verify no new categories were created
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 2

    # --- Test Saving Transactions ---

    def test_save_transactions_table_empty_dataframe(self, db_interface: DatabaseInterface):
        """Test saving empty DataFrame."""
        # Arrange
        df = pd.DataFrame(columns=['description', 'amount', 'transaction_date', 'category', 'sub_category'])
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is True
        assert len(db_interface.db.get_all_transactions()) == 0

    def test_save_transactions_table_missing_required_columns(self, db_interface: DatabaseInterface):
        """Test saving DataFrame with missing required columns."""
        # Arrange
        df = pd.DataFrame({
            'description': ['Coffee'],
            # Missing 'amount' and 'transaction_date'
        })
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is False

    def test_save_transactions_table_basic_transactions(self, db_interface: DatabaseInterface):
        """Test saving basic transactions without categories."""
        # Arrange
        df = pd.DataFrame({
            'description': ['Coffee', 'Lunch'],
            'amount': [5.50, 12.75],
            'transaction_date': ['2024-01-15 10:30:00', '2024-01-15 13:45:00'],
            'category': ['', ''],
            'sub_category': ['', '']
        })
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is True
        
        transactions = db_interface.db.get_all_transactions()
        assert len(transactions) == 2
        
        # Check transaction details
        descriptions = [t.description for t in transactions]
        assert 'Coffee' in descriptions
        assert 'Lunch' in descriptions
        
        amounts = [float(t.amount) for t in transactions]
        assert 5.50 in amounts
        assert 12.75 in amounts

    def test_save_transactions_table_with_existing_categories(self, db_interface: DatabaseInterface):
        """Test saving transactions with existing categories."""
        # Arrange
        food = db_interface.db.create_category(name="Food")
        groceries = db_interface.db.create_category(name="Groceries", parent_id=food.id)
        
        df = pd.DataFrame({
            'description': ['Restaurant', 'Supermarket'],
            'amount': [25.00, 45.75],
            'transaction_date': ['2024-01-15 19:30:00', '2024-01-16 10:15:00'],
            'category': ['Food', 'Food'],
            'sub_category': ['', 'Groceries']
        })
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is True
        
        transactions = db_interface.db.get_all_transactions()
        assert len(transactions) == 2
        
        # Check category assignments
        restaurant_tx = next(t for t in transactions if t.description == 'Restaurant')
        assert restaurant_tx.category_id == food.id
        
        supermarket_tx = next(t for t in transactions if t.description == 'Supermarket')
        assert supermarket_tx.category_id == groceries.id

    def test_save_transactions_table_auto_create_categories(self, db_interface: DatabaseInterface):
        """Test saving transactions with auto-creation of new categories."""
        # Arrange
        df = pd.DataFrame({
            'description': ['Movie ticket', 'Bus fare'],
            'amount': [15.00, 3.50],
            'transaction_date': ['2024-01-15 20:00:00', '2024-01-16 08:30:00'],
            'category': ['Entertainment', 'Transport'],
            'sub_category': ['', 'Public Transport']
        })
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is True
        
        # Check that categories were auto-created
        categories = db_interface.db.get_all_categories()
        category_names = [c.name for c in categories]
        assert 'Entertainment' in category_names
        assert 'Transport' in category_names
        assert 'Public Transport' in category_names
        
        # Check category hierarchy
        transport = next(c for c in categories if c.name == 'Transport')
        public_transport = next(c for c in categories if c.name == 'Public Transport')
        assert public_transport.parent_id == transport.id
        
        # Check transaction category assignments
        transactions = db_interface.db.get_all_transactions()
        movie_tx = next(t for t in transactions if t.description == 'Movie ticket')
        bus_tx = next(t for t in transactions if t.description == 'Bus fare')
        
        entertainment = next(c for c in categories if c.name == 'Entertainment')
        assert movie_tx.category_id == entertainment.id
        assert bus_tx.category_id == public_transport.id

    def test_save_transactions_table_mixed_datetime_formats(self, db_interface: DatabaseInterface):
        """Test saving transactions with different datetime formats."""
        # Arrange
        indian_tz = pytz.timezone("Asia/Kolkata")
        
        df = pd.DataFrame({
            'description': ['Coffee', 'Lunch', 'Dinner'],
            'amount': [5.50, 12.75, 18.25],
            'transaction_date': [
                '2024-01-15 10:30:00',  # String format
                pd.Timestamp('2024-01-15 13:45:00'),  # Pandas Timestamp
                indian_tz.localize(datetime.datetime(2024, 1, 15, 19, 30))  # Timezone-aware datetime
            ],
            'category': ['', '', ''],
            'sub_category': ['', '', '']
        })
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is True
        
        transactions = db_interface.db.get_all_transactions()
        assert len(transactions) == 3
        
        # Check that all transactions were saved with proper datetime values
        # Note: The actual timezone handling depends on the database implementation
        # For SQLite in-memory testing, timezone info might be stripped
        for transaction in transactions:
            assert isinstance(transaction.transaction_date, datetime.datetime)
            # Verify the dates are correct (regardless of timezone info in test DB)
            assert transaction.transaction_date.year == 2024
            assert transaction.transaction_date.month == 1
            assert transaction.transaction_date.day == 15

    def test_save_transactions_table_partial_failure_handling(self, db_interface: DatabaseInterface):
        """Test handling of partial failures when saving transactions."""
        # Arrange - Create a DataFrame with one invalid row (invalid amount)
        df = pd.DataFrame({
            'description': ['Valid transaction', 'Invalid transaction'],
            'amount': [25.50, 'invalid_amount'],  # Second amount is invalid
            'transaction_date': ['2024-01-15 10:30:00', '2024-01-15 11:30:00'],
            'category': ['', ''],
            'sub_category': ['', '']
        })
        
        # Act
        result = db_interface.save_transactions_table(df)
        
        # Assert
        assert result is False  # Should return False due to partial failure
        
        # Check that valid transaction was still saved
        transactions = db_interface.db.get_all_transactions()
        assert len(transactions) == 1
        assert transactions[0].description == 'Valid transaction'
        assert float(transactions[0].amount) == 25.50

    # --- End-to-End Real-World Scenario Tests ---

    def test_realistic_csv_import_with_errors_and_retry_creates_duplicates(self, db_interface: DatabaseInterface):
        """
        Test realistic scenario: User imports CSV, some rows fail, user fixes CSV and re-imports entire file.
        This tests the REAL behavior - duplicates WILL be created because the interface doesn't know 
        which rows were already saved.
        """
        # Step 1: User imports a CSV file with some problematic data
        csv_data = pd.DataFrame({
            'description': ['Coffee Shop', 'Invalid Amount Row', 'Grocery Store', 'Invalid Date Row', 'Gas Station'],
            'amount': [4.50, 'bad_amount', 67.89, 25.00, 'another_bad_amount'],
            'transaction_date': [
                '2024-01-15 08:30:00',
                '2024-01-15 09:15:00', 
                '2024-01-15 10:45:00',
                'bad_date_format',
                '2024-01-15 16:20:00'
            ],
            'category': ['Food', 'Food', 'Food', 'Transport', 'Transport'],
            'sub_category': ['', '', 'Groceries', '', '']
        })
        
        # User tries to save - some will fail
        result1 = db_interface.save_transactions_table(csv_data)
        assert result1 is False  # Should fail due to invalid data
        
        # Check what actually got saved (only valid rows)
        saved_transactions = db_interface.db.get_all_transactions()
        saved_count_first = len(saved_transactions)
        saved_descriptions_first = [t.description for t in saved_transactions]
        
        # Only valid transactions should be saved
        assert 'Coffee Shop' in saved_descriptions_first
        assert 'Grocery Store' in saved_descriptions_first
        assert 'Invalid Amount Row' not in saved_descriptions_first
        assert 'Invalid Date Row' not in saved_descriptions_first
        assert 'Gas Station' not in saved_descriptions_first
        assert saved_count_first == 2  # Only 2 valid transactions
        
        # Step 2: User fixes the CSV file and re-imports THE ENTIRE FILE
        # (This is realistic - users don't know which rows failed, so they fix and re-import everything)
        fixed_csv_data = pd.DataFrame({
            'description': ['Coffee Shop', 'Fixed Amount Row', 'Grocery Store', 'Fixed Date Row', 'Gas Station'],
            'amount': [4.50, 12.75, 67.89, 25.00, 45.60],  # All amounts now valid
            'transaction_date': [
                '2024-01-15 08:30:00',  # Same as before
                '2024-01-15 09:15:00',  # Same time, fixed amount
                '2024-01-15 10:45:00',  # Same as before  
                '2024-01-15 14:30:00',  # Fixed date
                '2024-01-15 16:20:00'   # Same as before
            ],
            'category': ['Food', 'Food', 'Food', 'Transport', 'Transport'],
            'sub_category': ['', '', 'Groceries', '', '']
        })
        
        # User re-imports entire file
        result2 = db_interface.save_transactions_table(fixed_csv_data)
        assert result2 is True  # Should succeed now
        
        # Step 3: Verify the REALISTIC outcome - duplicates exist!
        all_transactions = db_interface.db.get_all_transactions()
        all_descriptions = [t.description for t in all_transactions]
        
        # Should have 7 total transactions (2 from first + 5 from second)
        assert len(all_transactions) == 7
        
        # The previously saved transactions are now duplicated
        assert all_descriptions.count('Coffee Shop') == 2  # Duplicate!
        assert all_descriptions.count('Grocery Store') == 2  # Duplicate!
        
        # New transactions appear once
        assert all_descriptions.count('Fixed Amount Row') == 1
        assert all_descriptions.count('Fixed Date Row') == 1
        assert all_descriptions.count('Gas Station') == 1
        
        # Step 4: Verify this creates a real problem for the user
        transactions_df = db_interface.get_transactions_table()
        assert len(transactions_df) == 7
        
        # User would see duplicate transactions in their expense report
        coffee_transactions = transactions_df[transactions_df['description'] == 'Coffee Shop']
        assert len(coffee_transactions) == 2
        
        grocery_transactions = transactions_df[transactions_df['description'] == 'Grocery Store']
        assert len(grocery_transactions) == 2
        
        # This demonstrates the real-world problem: the interface allows duplicates
        # and users need to handle deduplication at the application level

    def test_realistic_batch_processing_failure_and_full_retry(self, db_interface: DatabaseInterface):
        """
        Test realistic batch processing scenario: Large batch fails partway through,
        entire batch is retried, creating duplicates for successful rows.
        """
        # Step 1: Create a batch of 20 transactions with errors scattered throughout
        batch_data = []
        for i in range(20):
            # Every 6th transaction has an error
            if i % 6 == 0:
                amount = 'error_amount'  # Invalid amount
            else:
                amount = 10.0 + i
            
            batch_data.append({
                'description': f'Batch Transaction {i+1}',
                'amount': amount,
                'transaction_date': f'2024-01-{(i % 28) + 1:02d} 10:00:00',
                'category': 'Food' if i % 2 == 0 else 'Transport',
                'sub_category': ''
            })
        
        batch_df = pd.DataFrame(batch_data)
        
        # Process the batch - should partially fail
        result1 = db_interface.save_transactions_table(batch_df)
        assert result1 is False
        
        # Count successful saves
        transactions_after_batch1 = db_interface.db.get_all_transactions()
        successful_count = len(transactions_after_batch1)
        
        # Should have saved 16 transactions (20 - 4 errors at positions 0, 6, 12, 18)
        assert successful_count == 16
        
        # Step 2: Fix the batch and retry ENTIRE batch (realistic behavior)
        fixed_batch_data = []
        for i in range(20):
            fixed_batch_data.append({
                'description': f'Batch Transaction {i+1}',
                'amount': 10.0 + i,  # All amounts now valid
                'transaction_date': f'2024-01-{(i % 28) + 1:02d} 10:00:00',
                'category': 'Food' if i % 2 == 0 else 'Transport',
                'sub_category': ''
            })
        
        fixed_batch_df = pd.DataFrame(fixed_batch_data)
        
        # Retry entire batch
        result2 = db_interface.save_transactions_table(fixed_batch_df)
        assert result2 is True
        
        # Step 3: Verify duplicates were created
        all_transactions = db_interface.db.get_all_transactions()
        
        # Should have 36 total transactions (16 successful from first + 20 from retry)
        assert len(all_transactions) == 36
        
        # Verify specific duplicates exist
        all_descriptions = [t.description for t in all_transactions]
        
        # Transactions that succeeded in first batch should appear twice
        assert all_descriptions.count('Batch Transaction 2') == 2  # Was successful first time
        assert all_descriptions.count('Batch Transaction 3') == 2  # Was successful first time
        
        # Transactions that failed first time should appear once
        assert all_descriptions.count('Batch Transaction 1') == 1  # Failed first time (index 0)
        assert all_descriptions.count('Batch Transaction 7') == 1  # Failed first time (index 6)
        
        # This demonstrates the real issue with batch retry scenarios

    def test_realistic_user_workflow_multiple_import_attempts(self, db_interface: DatabaseInterface):
        """
        Test realistic user workflow: User tries multiple times to import the same data
        with small fixes each time, creating multiple duplicates.
        """
        # Original data with multiple issues
        original_data = pd.DataFrame({
            'description': ['Morning Coffee', 'Lunch Special', 'Evening Snack'],
            'amount': [5.50, 'invalid', 3.25],
            'transaction_date': ['2024-01-15 08:00:00', '2024-01-15 12:00:00', 'bad_date'],
            'category': ['Food', 'Food', 'Food'],
            'sub_category': ['', 'Dining', '']
        })
        
        # Attempt 1: User tries original data
        result1 = db_interface.save_transactions_table(original_data)
        assert result1 is False
        
        transactions_after_1 = db_interface.db.get_all_transactions()
        assert len(transactions_after_1) == 1  # Only 'Morning Coffee' succeeds
        assert transactions_after_1[0].description == 'Morning Coffee'
        
        # Attempt 2: User fixes amount but not date
        attempt2_data = pd.DataFrame({
            'description': ['Morning Coffee', 'Lunch Special', 'Evening Snack'],
            'amount': [5.50, 12.75, 3.25],  # Fixed amount
            'transaction_date': ['2024-01-15 08:00:00', '2024-01-15 12:00:00', 'bad_date'],  # Date still bad
            'category': ['Food', 'Food', 'Food'],
            'sub_category': ['', 'Dining', '']
        })
        
        result2 = db_interface.save_transactions_table(attempt2_data)
        assert result2 is False  # Still fails due to bad date
        
        transactions_after_2 = db_interface.db.get_all_transactions()
        assert len(transactions_after_2) == 3  # 1 + 2 new successful (Morning Coffee duplicate + Lunch Special)
        
        # Attempt 3: User fixes date
        attempt3_data = pd.DataFrame({
            'description': ['Morning Coffee', 'Lunch Special', 'Evening Snack'],
            'amount': [5.50, 12.75, 3.25],
            'transaction_date': ['2024-01-15 08:00:00', '2024-01-15 12:00:00', '2024-01-15 18:00:00'],  # All fixed
            'category': ['Food', 'Food', 'Food'],
            'sub_category': ['', 'Dining', '']
        })
        
        result3 = db_interface.save_transactions_table(attempt3_data)
        assert result3 is True  # Finally succeeds
        
        # Final verification: Multiple duplicates exist
        final_transactions = db_interface.db.get_all_transactions()
        assert len(final_transactions) == 6  # 3 + 3 new
        
        final_descriptions = [t.description for t in final_transactions]
        
        # Morning Coffee appears 3 times (once per attempt)
        assert final_descriptions.count('Morning Coffee') == 3
        
        # Lunch Special appears 2 times (attempts 2 and 3)
        assert final_descriptions.count('Lunch Special') == 2
        
        # Evening Snack appears 1 time (only attempt 3)
        assert final_descriptions.count('Evening Snack') == 1
        
        # Verify through interface retrieval
        transactions_df = db_interface.get_transactions_table()
        assert len(transactions_df) == 6
        
        # This shows the cumulative effect of multiple import attempts
        coffee_entries = transactions_df[transactions_df['description'] == 'Morning Coffee']
        assert len(coffee_entries) == 3
        
        # All should have same amount and date (user didn't change these)
        assert all(coffee_entries['amount'] == 5.50)

    def test_realistic_concurrent_user_scenario_same_data(self, db_interface: DatabaseInterface):
        """
        Test scenario where the same transaction data might be imported multiple times
        (e.g., from different sources or by different users), creating duplicates.
        """
        # Same transaction data from two different sources
        source1_data = pd.DataFrame({
            'description': ['ATM Withdrawal', 'Grocery Shopping', 'Gas Fill-up'],
            'amount': [100.00, 45.67, 52.30],
            'transaction_date': ['2024-01-15 10:00:00', '2024-01-15 11:30:00', '2024-01-15 15:45:00'],
            'category': ['Cash', 'Food', 'Transport'],
            'sub_category': ['', 'Groceries', '']
        })
        
        # Import from source 1
        result1 = db_interface.save_transactions_table(source1_data)
        assert result1 is True
        
        # Same data from source 2 (e.g., bank export vs credit card export)
        source2_data = pd.DataFrame({
            'description': ['ATM Withdrawal', 'Grocery Shopping', 'Gas Fill-up'],
            'amount': [100.00, 45.67, 52.30],  # Exact same amounts
            'transaction_date': ['2024-01-15 10:00:00', '2024-01-15 11:30:00', '2024-01-15 15:45:00'],  # Same dates
            'category': ['Cash', 'Food', 'Transport'],  # Same categories
            'sub_category': ['', 'Groceries', '']
        })
        
        # Import from source 2
        result2 = db_interface.save_transactions_table(source2_data)
        assert result2 is True
        
        # Verify duplicates were created
        all_transactions = db_interface.db.get_all_transactions()
        assert len(all_transactions) == 6  # 3 + 3 duplicates
        
        all_descriptions = [t.description for t in all_transactions]
        assert all_descriptions.count('ATM Withdrawal') == 2
        assert all_descriptions.count('Grocery Shopping') == 2
        assert all_descriptions.count('Gas Fill-up') == 2
        
        # Verify through interface
        transactions_df = db_interface.get_transactions_table()
        assert len(transactions_df) == 6
        
        # Check that identical transactions exist
        atm_transactions = transactions_df[transactions_df['description'] == 'ATM Withdrawal']
        assert len(atm_transactions) == 2
        assert all(atm_transactions['amount'] == 100.00)
        
        # This demonstrates why deduplication logic is needed at the application level,
        # not in the database interface

    def test_realistic_data_validation_edge_cases_with_duplicates(self, db_interface: DatabaseInterface):
        """
        Test realistic edge cases in data validation that lead to duplicate scenarios.
        """
        # Step 1: Data with edge cases that might pass validation inconsistently
        edge_case_data = pd.DataFrame({
            'description': ['Zero Amount', 'Negative Amount', 'Very Large Amount', 'Empty Description'],
            'amount': [0.00, -50.00, 999999.99, 25.00],
            'transaction_date': ['2024-01-15 00:00:00', '2024-01-15 23:59:59', '2024-01-15 12:00:00', '2024-01-15 15:00:00'],
            'category': ['Food', 'Refund', 'Investment', ''],
            'sub_category': ['', '', '', '']
        })
        
        # Save edge case data
        result1 = db_interface.save_transactions_table(edge_case_data)
        assert result1 is True  # Should succeed (these are technically valid)
        
        # Step 2: User imports same data again (thinking it failed due to edge cases)
        result2 = db_interface.save_transactions_table(edge_case_data)
        assert result2 is True
        
        # Verify duplicates were created
        all_transactions = db_interface.db.get_all_transactions()
        assert len(all_transactions) == 8  # 4 + 4 duplicates
        
        all_descriptions = [t.description for t in all_transactions]
        assert all_descriptions.count('Zero Amount') == 2
        assert all_descriptions.count('Negative Amount') == 2
        assert all_descriptions.count('Very Large Amount') == 2
        assert all_descriptions.count('Empty Description') == 2
        
        # Verify through interface
        transactions_df = db_interface.get_transactions_table()
        assert len(transactions_df) == 8
        
        # Check that edge case values are preserved
        zero_amount_transactions = transactions_df[transactions_df['description'] == 'Zero Amount']
        assert len(zero_amount_transactions) == 2
        assert all(zero_amount_transactions['amount'] == 0.00)
        
        negative_amount_transactions = transactions_df[transactions_df['description'] == 'Negative Amount']
        assert len(negative_amount_transactions) == 2
        assert all(negative_amount_transactions['amount'] == -50.00)

    # --- Integration Tests ---

    def test_full_workflow_categories_and_transactions(self, db_interface: DatabaseInterface):
        """Test complete workflow: create categories, save transactions, retrieve data."""
        # Step 1: Create some initial categories
        result = db_interface.create_category_hierarchy("Food", "Groceries")
        assert result is True
        
        result = db_interface.create_category_hierarchy("Food", "Dining")
        assert result is True
        
        result = db_interface.create_category_hierarchy("Transport", "")
        assert result is True
        
        # Step 2: Save transactions with mix of existing and new categories
        transactions_df = pd.DataFrame({
            'description': ['Supermarket', 'Restaurant', 'Bus ticket', 'Movie'],
            'amount': [45.75, 28.50, 3.50, 15.00],
            'transaction_date': [
                '2024-01-15 10:00:00',
                '2024-01-15 19:30:00', 
                '2024-01-16 08:30:00',
                '2024-01-16 20:00:00'
            ],
            'category': ['Food', 'Food', 'Transport', 'Entertainment'],
            'sub_category': ['Groceries', 'Dining', '', '']
        })
        
        result = db_interface.save_transactions_table(transactions_df)
        assert result is True
        
        # Step 3: Retrieve and verify categories table
        categories_df = db_interface.get_categories_table()
        assert len(categories_df) == 5  # Food, Groceries, Dining, Transport, Entertainment
        
        # Step 4: Retrieve and verify transactions table
        retrieved_transactions_df = db_interface.get_transactions_table()
        assert len(retrieved_transactions_df) == 4
        
        # Verify the denormalized structure
        supermarket_row = retrieved_transactions_df[retrieved_transactions_df['description'] == 'Supermarket'].iloc[0]
        assert supermarket_row['category'] == 'Food'
        assert supermarket_row['sub_category'] == 'Groceries'
        
        restaurant_row = retrieved_transactions_df[retrieved_transactions_df['description'] == 'Restaurant'].iloc[0]
        assert restaurant_row['category'] == 'Food'
        assert restaurant_row['sub_category'] == 'Dining'
        
        bus_row = retrieved_transactions_df[retrieved_transactions_df['description'] == 'Bus ticket'].iloc[0]
        assert bus_row['category'] == 'Transport'
        assert bus_row['sub_category'] == ''
        
        movie_row = retrieved_transactions_df[retrieved_transactions_df['description'] == 'Movie'].iloc[0]
        assert movie_row['category'] == 'Entertainment'
        assert movie_row['sub_category'] == ''

    def test_interface_isolation_from_sql_details(self, db_interface: DatabaseInterface):
        """Test that the interface properly isolates users from SQL relationship complexity."""
        # This test verifies that users can work with simple denormalized DataFrames
        # without needing to understand foreign keys, joins, or SQL relationships
        
        # Step 1: User works with simple category names (no IDs)
        transactions_df = pd.DataFrame({
            'description': ['Grocery shopping', 'Fine dining'],
            'amount': [67.89, 125.50],
            'transaction_date': ['2024-01-20 11:00:00', '2024-01-20 20:30:00'],
            'category': ['Food', 'Food'],
            'sub_category': ['Groceries', 'Restaurants']
        })
        
        # Step 2: Interface handles all SQL complexity internally
        result = db_interface.save_transactions_table(transactions_df)
        assert result is True
        
        # Step 3: User gets back simple denormalized DataFrame
        retrieved_df = db_interface.get_transactions_table()
        assert len(retrieved_df) == 2
        
        # Verify user never sees foreign keys or SQL relationships
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(retrieved_df.columns) == expected_columns
        
        # Verify data integrity through the interface
        grocery_row = retrieved_df[retrieved_df['description'] == 'Grocery shopping'].iloc[0]
        assert grocery_row['category'] == 'Food'
        assert grocery_row['sub_category'] == 'Groceries'
        
        dining_row = retrieved_df[retrieved_df['description'] == 'Fine dining'].iloc[0]
        assert dining_row['category'] == 'Food'
        assert dining_row['sub_category'] == 'Restaurants'
        
        # Verify that behind the scenes, proper SQL relationships were created
        categories = db_interface.db.get_all_categories()
        food_category = next(c for c in categories if c.name == 'Food' and c.parent is None)
        groceries_category = next(c for c in categories if c.name == 'Groceries')
        restaurants_category = next(c for c in categories if c.name == 'Restaurants')
        
        assert groceries_category.parent_id == food_category.id
        assert restaurants_category.parent_id == food_category.id
        
        transactions = db_interface.db.get_all_transactions()
        assert all(t.category_id is not None for t in transactions)

    # --- Enhanced Atomic Transaction Tests ---

    def test_atomic_transaction_save_success(self, db_interface: DatabaseInterface):
        """Test that save_transactions_table uses atomic transactions successfully."""
        # Arrange
        transactions_df = pd.DataFrame({
            'description': ['Coffee', 'Lunch', 'Dinner'],
            'amount': [5.50, 12.75, 18.25],
            'transaction_date': ['2024-01-15 08:00:00', '2024-01-15 12:00:00', '2024-01-15 19:00:00'],
            'category': ['Food', 'Food', 'Food'],
            'sub_category': ['', 'Dining', 'Dining']
        })
        
        # Act
        result = db_interface.save_transactions_table(transactions_df)
        
        # Assert
        assert result is True
        
        # Verify all transactions were saved atomically
        saved_transactions = db_interface.db.get_all_transactions()
        assert len(saved_transactions) == 3
        
        # Verify categories were created atomically
        categories = db_interface.db.get_all_categories()
        category_names = [c.name for c in categories]
        assert 'Food' in category_names
        assert 'Dining' in category_names
        
        # Verify hierarchy was created correctly
        dining_category = next(c for c in categories if c.name == 'Dining')
        food_category = next(c for c in categories if c.name == 'Food')
        assert dining_category.parent_id == food_category.id

    def test_atomic_transaction_rollback_on_error(self, db_interface: DatabaseInterface):
        """Test that atomic transactions rollback completely on error."""
        # Arrange - Create a DataFrame with one invalid row that will cause failure
        transactions_df = pd.DataFrame({
            'description': ['Valid Coffee', 'Invalid Amount', 'Valid Lunch'],
            'amount': [5.50, 'not_a_number', 12.75],  # Middle row has invalid amount
            'transaction_date': ['2024-01-15 08:00:00', '2024-01-15 09:00:00', '2024-01-15 12:00:00'],
            'category': ['Food', 'Food', 'Food'],
            'sub_category': ['', '', '']
        })
        
        # Act
        result = db_interface.save_transactions_table(transactions_df)
        
        # Assert
        assert result is False  # Should fail due to invalid data
        
        # Verify NO transactions were saved (complete rollback)
        saved_transactions = db_interface.db.get_all_transactions()
        assert len(saved_transactions) == 0
        
        # Verify NO categories were created (complete rollback)
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 0

    def test_atomic_transaction_with_category_creation(self, db_interface: DatabaseInterface):
        """Test atomic transaction with automatic category hierarchy creation."""
        # Arrange
        transactions_df = pd.DataFrame({
            'description': ['Grocery shopping', 'Restaurant dinner', 'Bus ticket'],
            'amount': [67.89, 125.50, 3.50],
            'transaction_date': ['2024-01-20 11:00:00', '2024-01-20 20:30:00', '2024-01-21 08:30:00'],
            'category': ['Food', 'Food', 'Transport'],
            'sub_category': ['Groceries', 'Dining', '']
        })
        
        # Act
        result = db_interface.save_transactions_table(transactions_df)
        
        # Assert
        assert result is True
        
        # Verify all transactions and categories were created atomically
        saved_transactions = db_interface.db.get_all_transactions()
        assert len(saved_transactions) == 3
        
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 4  # Food, Groceries, Dining, Transport
        
        # Verify hierarchy was created correctly in atomic operation
        food_category = next(c for c in categories if c.name == 'Food' and c.parent is None)
        groceries_category = next(c for c in categories if c.name == 'Groceries')
        dining_category = next(c for c in categories if c.name == 'Dining')
        transport_category = next(c for c in categories if c.name == 'Transport' and c.parent is None)
        
        assert groceries_category.parent_id == food_category.id
        assert dining_category.parent_id == food_category.id
        assert transport_category.parent is None

    def test_session_aware_category_resolution(self, db_interface: DatabaseInterface):
        """Test that category resolution works within session context."""
        # Arrange - Create some existing categories
        existing_food = db_interface.db.create_category(name="Food")
        existing_groceries = db_interface.db.create_category(name="Groceries", parent_id=existing_food.id)
        
        # Test _resolve_category_id with session
        session = db_interface.db.get_session()
        
        # Act & Assert
        # Test resolving existing top-level category
        food_id = db_interface._resolve_category_id("Food", "", session=session)
        assert food_id == existing_food.id
        
        # Test resolving existing sub-category
        groceries_id = db_interface._resolve_category_id("Food", "Groceries", session=session)
        assert groceries_id == existing_groceries.id
        
        # Test resolving non-existent category
        nonexistent_id = db_interface._resolve_category_id("NonExistent", "", session=session)
        assert nonexistent_id is None
        
        # Test resolving non-existent sub-category
        nonexistent_sub_id = db_interface._resolve_category_id("Food", "NonExistent", session=session)
        assert nonexistent_sub_id is None

    def test_create_category_hierarchy_in_session(self, db_interface: DatabaseInterface):
        """Test category hierarchy creation within session context."""
        # Arrange
        session = db_interface.db.get_session()
        
        # Act - Create hierarchy within session
        result = db_interface._create_category_hierarchy_in_session("Food", "Restaurants", session)
        session.commit()  # Manual commit for test
        
        # Assert
        assert result is True
        
        # Verify categories were created
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 2
        
        food_category = next(c for c in categories if c.name == 'Food')
        restaurants_category = next(c for c in categories if c.name == 'Restaurants')
        
        assert food_category.parent is None
        assert restaurants_category.parent_id == food_category.id

    def test_create_category_hierarchy_in_session_with_existing_parent(self, db_interface: DatabaseInterface):
        """Test category hierarchy creation when parent already exists."""
        # Arrange - Create parent category first
        existing_food = db_interface.db.create_category(name="Food")
        session = db_interface.db.get_session()
        
        # Act - Create sub-category with existing parent
        result = db_interface._create_category_hierarchy_in_session("Food", "Snacks", session)
        session.commit()
        
        # Assert
        assert result is True
        
        # Verify only one new category was created
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 2
        
        # Verify the existing parent was used
        snacks_category = next(c for c in categories if c.name == 'Snacks')
        assert snacks_category.parent_id == existing_food.id

    # --- Enhanced Error Handling Tests ---

    def test_error_handling_with_constraint_classification(self, db_interface: DatabaseInterface):
        """Test that error handling classifies constraint errors properly."""
        # This test verifies that the interface can handle and classify different types of errors
        # We'll test the error handling methods directly since they're part of the interface
        
        # Test constraint error handling
        integrity_error = IntegrityError("UNIQUE constraint failed", None, None)
        error_info = db_interface.db.handle_constraint_error(integrity_error)
        
        assert error_info["error_category"] == "constraint_violation"
        assert error_info["constraint_type"] == "unique_violation"
        assert error_info["is_retryable"] is False

    def test_retryable_error_detection(self, db_interface: DatabaseInterface):
        """Test retryable error detection in the interface."""
        # Test operational errors (retryable)
        operational_error = OperationalError("database is locked", None, None)
        assert db_interface.db.is_retryable_error(operational_error) is True
        
        # Test integrity errors (not retryable)
        integrity_error = IntegrityError("constraint failed", None, None)
        assert db_interface.db.is_retryable_error(integrity_error) is False

    def test_save_transactions_with_detailed_error_logging(self, db_interface: DatabaseInterface):
        """Test that save_transactions_table provides detailed error information."""
        # Arrange - Create DataFrame with various error types
        problematic_df = pd.DataFrame({
            'description': ['Valid', 'Invalid Date', 'Invalid Amount'],
            'amount': [25.50, 30.00, 'not_a_number'],
            'transaction_date': ['2024-01-15 10:00:00', 'invalid_date_format', '2024-01-15 12:00:00'],
            'category': ['Food', 'Food', 'Food'],
            'sub_category': ['', '', '']
        })
        
        # Act
        result = db_interface.save_transactions_table(problematic_df)
        
        # Assert
        assert result is False  # Should fail due to errors
        
        # Verify no partial saves occurred (atomic rollback)
        saved_transactions = db_interface.db.get_all_transactions()
        assert len(saved_transactions) == 0

    def test_empty_dataframe_handling(self, db_interface: DatabaseInterface):
        """Test handling of empty DataFrames."""
        # Arrange
        empty_df = pd.DataFrame(columns=['description', 'amount', 'transaction_date', 'category', 'sub_category'])
        
        # Act
        result = db_interface.save_transactions_table(empty_df)
        
        # Assert
        assert result is True  # Empty DataFrame should be handled gracefully
        assert len(db_interface.db.get_all_transactions()) == 0

    def test_missing_required_columns_error_handling(self, db_interface: DatabaseInterface):
        """Test error handling for missing required columns."""
        # Arrange
        invalid_df = pd.DataFrame({
            'description': ['Coffee'],
            'category': ['Food']
            # Missing 'amount' and 'transaction_date'
        })
        
        # Act
        result = db_interface.save_transactions_table(invalid_df)
        
        # Assert
        assert result is False  # Should fail due to missing required columns
        assert len(db_interface.db.get_all_transactions()) == 0

    # --- Session-Aware Operations Tests ---

    def test_get_categories_table_with_session_isolation(self, db_interface: DatabaseInterface):
        """Test that get_categories_table works correctly with session isolation."""
        # Arrange - Create categories
        food = db_interface.db.create_category(name="Food")
        groceries = db_interface.db.create_category(name="Groceries", parent_id=food.id)
        
        # Act
        categories_df = db_interface.get_categories_table()
        
        # Assert
        assert len(categories_df) == 2
        assert 'Food' in categories_df['name'].values
        assert 'Groceries' in categories_df['name'].values
        
        # Verify hierarchy is correctly represented
        groceries_row = categories_df[categories_df['name'] == 'Groceries'].iloc[0]
        assert groceries_row['parent_category'] == 'Food'

    def test_get_transactions_table_with_session_isolation(self, db_interface: DatabaseInterface):
        """Test that get_transactions_table works correctly with session isolation."""
        # Arrange - Create categories and transactions
        food = db_interface.db.create_category(name="Food")
        dining = db_interface.db.create_category(name="Dining", parent_id=food.id)
        
        indian_tz = pytz.timezone("Asia/Kolkata")
        transaction_date = indian_tz.localize(datetime.datetime(2024, 1, 15, 12, 0))
        
        db_interface.db.create_transaction(
            amount=25.50,
            transaction_date=transaction_date,
            description="Restaurant lunch",
            category_id=dining.id
        )
        
        # Act
        transactions_df = db_interface.get_transactions_table()
        
        # Assert
        assert len(transactions_df) == 1
        transaction_row = transactions_df.iloc[0]
        assert transaction_row['description'] == "Restaurant lunch"
        assert transaction_row['category'] == 'Food'
        assert transaction_row['sub_category'] == 'Dining'
        assert transaction_row['amount'] == 25.50

    # --- Batch Operations with Atomic Transactions Tests ---

    def test_large_batch_atomic_operation(self, db_interface: DatabaseInterface):
        """Test atomic operation with larger batch of transactions."""
        # Arrange - Create a larger dataset
        num_transactions = 50
        transactions_data = []
        
        for i in range(num_transactions):
            transactions_data.append({
                'description': f'Transaction {i+1}',
                'amount': 10.0 + i,
                'transaction_date': f'2024-01-{(i % 28) + 1:02d} 10:00:00',
                'category': 'Food' if i % 2 == 0 else 'Transport',
                'sub_category': 'Groceries' if i % 4 == 0 else ''
            })
        
        batch_df = pd.DataFrame(transactions_data)
        
        # Act
        result = db_interface.save_transactions_table(batch_df)
        
        # Assert
        assert result is True
        
        # Verify all transactions were saved atomically
        saved_transactions = db_interface.db.get_all_transactions()
        assert len(saved_transactions) == num_transactions
        
        # Verify categories were created
        categories = db_interface.db.get_all_categories()
        category_names = [c.name for c in categories]
        assert 'Food' in category_names
        assert 'Transport' in category_names
        assert 'Groceries' in category_names

    def test_mixed_category_hierarchy_atomic_creation(self, db_interface: DatabaseInterface):
        """Test atomic creation of complex category hierarchies."""
        # Arrange
        transactions_df = pd.DataFrame({
            'description': ['Supermarket', 'Fine dining', 'Bus pass', 'Movie ticket', 'Coffee'],
            'amount': [67.89, 125.50, 45.00, 15.00, 4.50],
            'transaction_date': [
                '2024-01-15 10:00:00', '2024-01-15 20:00:00', '2024-01-16 08:00:00',
                '2024-01-16 19:00:00', '2024-01-17 09:00:00'
            ],
            'category': ['Food', 'Food', 'Transport', 'Entertainment', 'Food'],
            'sub_category': ['Groceries', 'Dining', 'Public Transport', '', 'Coffee Shops']
        })
        
        # Act
        result = db_interface.save_transactions_table(transactions_df)
        
        # Assert
        assert result is True
        
        # Verify complex hierarchy was created atomically
        categories = db_interface.db.get_all_categories()
        assert len(categories) == 6  # Food, Groceries, Dining, Coffee Shops, Transport, Public Transport, Entertainment
        
        # Verify hierarchy relationships
        food_category = next(c for c in categories if c.name == 'Food' and c.parent is None)
        transport_category = next(c for c in categories if c.name == 'Transport' and c.parent is None)
        entertainment_category = next(c for c in categories if c.name == 'Entertainment' and c.parent is None)
        
        groceries_category = next(c for c in categories if c.name == 'Groceries')
        dining_category = next(c for c in categories if c.name == 'Dining')
        coffee_shops_category = next(c for c in categories if c.name == 'Coffee Shops')
        public_transport_category = next(c for c in categories if c.name == 'Public Transport')
        
        assert groceries_category.parent_id == food_category.id
        assert dining_category.parent_id == food_category.id
        assert coffee_shops_category.parent_id == food_category.id
        assert public_transport_category.parent_id == transport_category.id
        assert entertainment_category.parent is None