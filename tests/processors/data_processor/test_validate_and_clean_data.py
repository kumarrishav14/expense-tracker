"""
Data validation and cleaning tests for DataProcessor.

Tests data cleaning and validation operations.
"""

import pandas as pd
import pytest
from datetime import datetime


class TestValidateAndCleanData:
    """Test data validation and cleaning functionality."""
    
    def test_date_parsing_standard_formats(self, data_processor):
        """Test parsing of various standard date formats."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '15/01/2024', '01-15-2024', '15-Jan-2024'],
            'description': ['Trans 1', 'Trans 2', 'Trans 3', 'Trans 4'],
            'amount': [1000.00, 2000.00, 3000.00, 4000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify all dates were parsed successfully
        assert len(result) == 4
        assert pd.api.types.is_datetime64_any_dtype(result['transaction_date'])
        
        # Verify no null dates
        assert not result['transaction_date'].isnull().any()
    
    def test_invalid_date_removal(self, data_processor):
        """Test removal of rows with unparseable dates."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', 'invalid_date', '2024-01-17', ''],
            'description': ['Valid 1', 'Invalid', 'Valid 2', 'Empty Date'],
            'amount': [1000.00, 2000.00, 3000.00, 4000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify invalid date rows were removed
        assert len(result) == 2  # Only 2 valid dates
        assert 'Invalid' not in result['description'].values
        assert 'Empty Date' not in result['description'].values
    
    def test_amount_currency_symbol_removal(self, data_processor):
        """Test removal of currency symbols from amount fields."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'description': ['Trans 1', 'Trans 2', 'Trans 3'],
            'amount': ['Rs 1,500.50', '₹ 2,000.00', '$150.75']
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify currency symbols were removed and amounts are numeric
        assert result['amount'].dtype in ['float64', 'int64']
        assert abs(result['amount'].iloc[0] - 1500.50) < 0.01
        assert abs(result['amount'].iloc[1] - 2000.00) < 0.01
        assert abs(result['amount'].iloc[2] - 150.75) < 0.01
    
    def test_amount_comma_removal(self, data_processor):
        """Test removal of commas from amount fields."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['Trans 1', 'Trans 2'],
            'amount': ['1,500.50', '10,000.00']
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify commas were removed
        assert abs(result['amount'].iloc[0] - 1500.50) < 0.01
        assert abs(result['amount'].iloc[1] - 10000.00) < 0.01
    
    def test_invalid_amount_removal(self, data_processor):
        """Test removal of rows with unparseable amounts."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'description': ['Valid', 'Invalid Amount', 'Valid 2'],
            'amount': [1000.00, 'not_a_number', 2000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify invalid amount row was removed
        assert len(result) == 2
        assert 'Invalid Amount' not in result['description'].values
    
    def test_description_whitespace_cleaning(self, data_processor):
        """Test cleaning of whitespace in description fields."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['  Transaction 1  ', '\tTransaction 2\n'],
            'amount': [1000.00, 2000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify whitespace was cleaned
        assert result['description'].iloc[0] == 'Transaction 1'
        assert result['description'].iloc[1] == 'Transaction 2'
    
    def test_empty_description_removal(self, data_processor):
        """Test removal of rows with empty descriptions."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'description': ['Valid Transaction', '', '   '],
            'amount': [1000.00, 2000.00, 3000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify empty description rows were removed
        assert len(result) == 1
        assert result['description'].iloc[0] == 'Valid Transaction'
    
    def test_duplicate_transaction_removal(self, data_processor):
        """Test removal of duplicate transactions."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-15', '2024-01-16'],
            'description': ['Amazon Purchase', 'Amazon Purchase', 'Different Purchase'],
            'amount': [1500.50, 1500.50, 2000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify duplicate was removed
        assert len(result) == 2
        amazon_purchases = result[result['description'] == 'Amazon Purchase']
        assert len(amazon_purchases) == 1
    
    def test_numeric_amount_conversion(self, data_processor):
        """Test conversion of string amounts to numeric."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['Trans 1', 'Trans 2'],
            'amount': ['1500.50', '2000']  # String amounts
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify amounts are now numeric
        assert result['amount'].dtype in ['float64', 'int64']
        assert isinstance(result['amount'].iloc[0], (int, float))
        assert isinstance(result['amount'].iloc[1], (int, float))
    
    def test_all_invalid_data_error(self, data_processor):
        """Test error when all rows are invalid after cleaning."""
        test_data = pd.DataFrame({
            'transaction_date': ['invalid_date', 'another_invalid'],
            'description': ['Trans 1', 'Trans 2'],
            'amount': [1000.00, 2000.00]
        })
        
        with pytest.raises(ValueError, match="All rows were removed during data cleaning"):
            data_processor.validate_and_clean_data(test_data)
    
    def test_mixed_valid_invalid_data(self, data_processor):
        """Test processing of mixed valid and invalid data."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', 'invalid_date', '2024-01-17', ''],
            'description': ['Valid 1', 'Invalid Date', 'Valid 2', 'Empty Date'],
            'amount': [1000.00, 'invalid_amount', 3000.00, 4000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Should keep only the first valid row (Valid 1)
        # Second row has invalid date, third row is valid, fourth has empty date
        assert len(result) >= 1  # At least one valid row should remain
        assert 'Valid 1' in result['description'].values
    
    def test_date_type_conversion(self, data_processor):
        """Test proper datetime type conversion."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['Trans 1', 'Trans 2'],
            'amount': [1000.00, 2000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify transaction_date is datetime type
        assert pd.api.types.is_datetime64_any_dtype(result['transaction_date'])
        
        # Verify specific datetime values
        assert isinstance(result['transaction_date'].iloc[0], pd.Timestamp)
    
    def test_preserve_valid_data_integrity(self, data_processor):
        """Test that valid data is preserved exactly during cleaning."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['Amazon Purchase', 'Salary Credit'],
            'amount': [1500.50, 50000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Verify all data preserved
        assert len(result) == 2
        assert 'Amazon Purchase' in result['description'].values
        assert 'Salary Credit' in result['description'].values
        assert 1500.50 in result['amount'].values
        assert 50000.00 in result['amount'].values
    
    def test_zero_amount_handling(self, data_processor):
        """Test handling of zero amounts."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['Zero Amount', 'Valid Amount'],
            'amount': [0.00, 1000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Zero amounts should be preserved (they're valid)
        assert len(result) == 2
        assert 0.00 in result['amount'].values
    
    def test_negative_amount_handling(self, data_processor):
        """Test handling of negative amounts."""
        test_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', '2024-01-16'],
            'description': ['Negative Amount', 'Positive Amount'],
            'amount': [-1000.00, 2000.00]
        })
        
        result = data_processor.validate_and_clean_data(test_data)
        
        # Negative amounts should be preserved (they're valid for debits)
        assert len(result) == 2
        assert -1000.00 in result['amount'].values
        assert 2000.00 in result['amount'].values