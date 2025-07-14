"""
AI categorization tests for DataProcessor.

Tests rule-based categorization logic.
"""

import pandas as pd
import pytest


class TestAddAiCategories:
    """Test AI categorization functionality."""
    
    def test_keyword_matching_food_dining(self, data_processor, mock_ai_categorization):
        """Test categorization of food and dining transactions."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16', '2024-01-17']),
            'description': ['Swiggy Food Order', 'Restaurant Bill Payment', 'Zomato Delivery'],
            'amount': [450.75, 1200.00, 350.50],
            'category': [None, None, None],
            'sub_category': [None, None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify food & dining categorization
        assert result['category'].iloc[0] == 'Food & Dining'
        assert result['category'].iloc[1] == 'Food & Dining'
        assert result['category'].iloc[2] == 'Food & Dining'
    
    def test_keyword_matching_transportation(self, data_processor, mock_ai_categorization):
        """Test categorization of transportation transactions."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'description': ['Uber Ride Payment', 'Metro Card Recharge'],
            'amount': [250.00, 500.00],
            'category': [None, None],
            'sub_category': [None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify transportation categorization
        assert result['category'].iloc[0] == 'Transportation'
        assert result['category'].iloc[1] == 'Transportation'
    
    def test_keyword_matching_shopping(self, data_processor, mock_ai_categorization):
        """Test categorization of shopping transactions."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'description': ['Amazon Purchase', 'Flipkart Shopping'],
            'amount': [1500.00, 2500.00],
            'category': [None, None],
            'sub_category': [None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify shopping categorization
        assert result['category'].iloc[0] == 'Shopping'
        assert result['category'].iloc[1] == 'Shopping'
    
    def test_default_category_assignment(self, data_processor, mock_ai_categorization):
        """Test assignment of default 'Other' category for unmatched descriptions."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['Unknown Merchant Transaction'],
            'amount': [1000.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify default category assignment
        assert result['category'].iloc[0] == 'Other'
    
    def test_case_insensitive_keyword_matching(self, data_processor, mock_ai_categorization):
        """Test that keyword matching is case insensitive."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'description': ['AMAZON PURCHASE', 'swiggy food order'],
            'amount': [1500.00, 450.00],
            'category': [None, None],
            'sub_category': [None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify case insensitive matching
        assert result['category'].iloc[0] == 'Shopping'
        assert result['category'].iloc[1] == 'Food & Dining'
    
    def test_existing_category_preservation(self, data_processor, mock_ai_categorization):
        """Test that existing categories are not overwritten."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'description': ['Amazon Purchase', 'Swiggy Order'],
            'amount': [1500.00, 450.00],
            'category': ['Manual Category', None],  # First has existing category
            'sub_category': [None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify existing category preserved, new category assigned
        assert result['category'].iloc[0] == 'Manual Category'
        assert result['category'].iloc[1] == 'Food & Dining'
    
    def test_sub_category_assignment_by_amount(self, data_processor, mock_ai_categorization):
        """Test sub-category assignment based on transaction amount."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16', '2024-01-17']),
            'description': ['Small Purchase', 'Regular Purchase', 'Large Purchase'],
            'amount': [50.00, 1500.00, 15000.00],  # Small, Regular, Large
            'category': [None, None, None],
            'sub_category': [None, None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify sub-category assignment by amount
        assert result['sub_category'].iloc[0] == 'Small Transaction'  # < 100
        assert result['sub_category'].iloc[1] == 'Regular Transaction'  # 100-10000
        assert result['sub_category'].iloc[2] == 'Large Transaction'  # > 10000
    
    def test_multiple_keyword_categories_first_match(self, data_processor, mock_ai_categorization):
        """Test that first matching category is assigned when multiple keywords match."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['Amazon Food Purchase'],  # Could match both Shopping and Food
            'amount': [500.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Should match first category found (order depends on iteration)
        assert result['category'].iloc[0] in ['Shopping', 'Food & Dining']
    
    def test_atm_category_assignment(self, data_processor, mock_ai_categorization):
        """Test ATM transaction categorization."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['ATM Cash Withdrawal'],
            'amount': [2000.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify ATM categorization
        assert result['category'].iloc[0] == 'ATM'
    
    def test_salary_category_assignment(self, data_processor, mock_ai_categorization):
        """Test salary transaction categorization."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['Monthly Salary Credit'],
            'amount': [50000.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify salary categorization
        assert result['category'].iloc[0] == 'Salary'
    
    def test_transfer_category_assignment(self, data_processor, mock_ai_categorization):
        """Test transfer transaction categorization."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['UPI Transfer to John'],
            'amount': [5000.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify transfer categorization
        assert result['category'].iloc[0] == 'Transfer'
    
    def test_bills_utilities_category_assignment(self, data_processor, mock_ai_categorization):
        """Test bills and utilities categorization."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16']),
            'description': ['Electricity Bill Payment', 'Internet Bill'],
            'amount': [1500.00, 800.00],
            'category': [None, None],
            'sub_category': [None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify bills & utilities categorization
        assert result['category'].iloc[0] == 'Bills & Utilities'
        assert result['category'].iloc[1] == 'Bills & Utilities'
    
    def test_healthcare_category_assignment(self, data_processor, mock_ai_categorization):
        """Test healthcare transaction categorization."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['Medical Store Purchase'],
            'amount': [500.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify healthcare categorization
        assert result['category'].iloc[0] == 'Healthcare'
    
    def test_entertainment_category_assignment(self, data_processor, mock_ai_categorization):
        """Test entertainment transaction categorization."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['Netflix Subscription'],
            'amount': [500.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify entertainment categorization
        assert result['category'].iloc[0] == 'Entertainment'
    
    def test_empty_description_handling(self, data_processor, mock_ai_categorization):
        """Test handling of empty or null descriptions."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': [''],
            'amount': [1000.00],
            'category': [None],
            'sub_category': [None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Should assign default category for empty description
        assert result['category'].iloc[0] == 'Other'
    
    def test_category_columns_initialization(self, data_processor, mock_ai_categorization):
        """Test that category columns are properly initialized if missing."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15']),
            'description': ['Test Transaction'],
            'amount': [1000.00]
            # Missing category and sub_category columns
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify category columns were added
        assert 'category' in result.columns
        assert 'sub_category' in result.columns
        assert result['category'].iloc[0] == 'Other'
        assert result['sub_category'].iloc[0] == 'Regular Transaction'
    
    def test_boundary_amount_sub_categories(self, data_processor, mock_ai_categorization):
        """Test sub-category assignment at boundary amounts."""
        test_data = pd.DataFrame({
            'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16', '2024-01-17']),
            'description': ['Boundary 1', 'Boundary 2', 'Boundary 3'],
            'amount': [100.00, 10000.00, 99.99],  # Boundary cases
            'category': [None, None, None],
            'sub_category': [None, None, None]
        })
        
        result = data_processor.add_ai_categories(test_data)
        
        # Verify boundary sub-category assignments
        assert result['sub_category'].iloc[0] == 'Regular Transaction'  # 100.00
        assert result['sub_category'].iloc[1] == 'Regular Transaction'  # 10000.00
        assert result['sub_category'].iloc[2] == 'Small Transaction'   # 99.99