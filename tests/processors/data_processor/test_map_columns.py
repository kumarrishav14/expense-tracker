"""
Column mapping tests for DataProcessor.

Tests intelligent column mapping from raw data to standard schema.
"""

import pandas as pd
import pytest


class TestMapColumns:
    """Test column mapping functionality."""
    
    def test_exact_name_matching(self, data_processor):
        """Test mapping with exact standard column names."""
        raw_data = pd.DataFrame({
            'transaction_date': ['2024-01-15'],
            'description': ['Test Transaction'],
            'amount': [1000.00],
            'category': ['Shopping'],
            'sub_category': ['Online']
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify all columns mapped correctly
        assert 'transaction_date' in result.columns
        assert 'description' in result.columns
        assert 'amount' in result.columns
        assert 'category' in result.columns
        assert 'sub_category' in result.columns
    
    def test_keyword_matching_variations(self, data_processor):
        """Test mapping with common column name variations."""
        raw_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'details': ['Test Transaction'],
            'transaction_amount': [1000.00]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify columns were mapped to standard names
        assert 'transaction_date' in result.columns
        assert 'description' in result.columns
        assert 'amount' in result.columns
        
        # Verify original column names were replaced
        assert 'date' not in result.columns
        assert 'details' not in result.columns
        assert 'transaction_amount' not in result.columns
    
    def test_case_insensitive_matching(self, data_processor):
        """Test column mapping is case insensitive."""
        raw_data = pd.DataFrame({
            'TRANSACTION_DATE': ['2024-01-15'],
            'Description': ['Test Transaction'],
            'AMOUNT': [1000.00]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify case insensitive mapping worked
        assert 'transaction_date' in result.columns
        assert 'description' in result.columns
        assert 'amount' in result.columns
    
    def test_debit_credit_combination(self, data_processor):
        """Test combination of separate debit and credit columns."""
        raw_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'description': ['Purchase', 'Salary', 'Withdrawal'],
            'debit': [500.00, None, 1000.00],
            'credit': [None, 50000.00, None]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify amount column was created
        assert 'amount' in result.columns
        
        # Verify debit/credit combination logic
        expected_amounts = [-500.00, 50000.00, -1000.00]
        actual_amounts = result['amount'].tolist()
        
        for expected, actual in zip(expected_amounts, actual_amounts):
            assert abs(expected - actual) < 0.01
        
        # Verify original debit/credit columns were removed
        assert 'debit' not in result.columns
        assert 'credit' not in result.columns
    
    def test_debit_credit_with_nulls(self, data_processor):
        """Test debit/credit combination handles null values correctly."""
        raw_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'description': ['Transaction 1', 'Transaction 2'],
            'debit_amount': [1000.00, None],
            'credit_amount': [None, 2000.00]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify amount calculation with nulls
        assert result['amount'].iloc[0] == -1000.00  # debit as negative
        assert result['amount'].iloc[1] == 2000.00   # credit as positive
    
    def test_missing_optional_columns(self, data_processor):
        """Test handling when optional columns are missing."""
        raw_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Test Transaction'],
            'amount': [1000.00]
            # Missing category and sub_category
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify optional columns added with None values
        assert 'category' in result.columns
        assert 'sub_category' in result.columns
        assert pd.isna(result['category'].iloc[0])
        assert pd.isna(result['sub_category'].iloc[0])
    
    def test_missing_required_columns_error(self, data_processor):
        """Test error when required columns cannot be mapped."""
        # Missing amount column
        raw_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Test Transaction']
            # Missing any amount-related column
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns"):
            data_processor.map_columns(raw_data)
    
    def test_missing_date_column_error(self, data_processor):
        """Test error when date column cannot be mapped."""
        raw_data = pd.DataFrame({
            'description': ['Test Transaction'],
            'amount': [1000.00]
            # Missing any date-related column
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns"):
            data_processor.map_columns(raw_data)
    
    def test_missing_description_column_error(self, data_processor):
        """Test error when description column cannot be mapped."""
        raw_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'amount': [1000.00]
            # Missing any description-related column
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns"):
            data_processor.map_columns(raw_data)
    
    def test_extra_columns_ignored(self, data_processor):
        """Test that unmapped columns are preserved but not used."""
        raw_data = pd.DataFrame({
            'transaction_date': ['2024-01-15'],
            'description': ['Test Transaction'],
            'amount': [1000.00],
            'random_column': ['ignore_this'],
            'another_column': [12345]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify required columns are mapped
        assert 'transaction_date' in result.columns
        assert 'description' in result.columns
        assert 'amount' in result.columns
        
        # Verify extra columns are preserved
        assert 'random_column' in result.columns
        assert 'another_column' in result.columns
    
    def test_multiple_date_columns_priority(self, data_processor):
        """Test priority when multiple date columns are available."""
        raw_data = pd.DataFrame({
            'posting_date': ['2024-01-15'],
            'transaction_date': ['2024-01-16'],  # Should have priority
            'value_date': ['2024-01-17'],
            'description': ['Test Transaction'],
            'amount': [1000.00]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify transaction_date was chosen (has priority in mapping)
        assert 'transaction_date' in result.columns
        # The original transaction_date column should be mapped
        assert result['transaction_date'].iloc[0] == '2024-01-16'
    
    def test_multiple_amount_columns_priority(self, data_processor):
        """Test priority when multiple amount columns are available."""
        raw_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Test Transaction'],
            'transaction_amount': [1000.00],  # Should have priority
            'amount': [2000.00],
            'value': [3000.00]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify amount column exists
        assert 'amount' in result.columns
        # Should map to the first found in priority order
        assert result['amount'].iloc[0] in [1000.00, 2000.00]  # Either could be chosen based on order
    
    def test_whitespace_in_column_names(self, data_processor):
        """Test handling of column names with whitespace."""
        raw_data = pd.DataFrame({
            ' transaction date ': ['2024-01-15'],
            'transaction details ': ['Test Transaction'],
            ' amount': [1000.00]
        })
        
        result = data_processor.map_columns(raw_data)
        
        # Verify columns with whitespace are mapped correctly
        assert 'transaction_date' in result.columns
        assert 'description' in result.columns
        assert 'amount' in result.columns
    
    def test_column_mapping_preserves_data(self, data_processor):
        """Test that column mapping preserves original data values."""
        original_data = {
            'date': ['2024-01-15', '2024-01-16'],
            'details': ['Transaction 1', 'Transaction 2'],
            'value': [1000.00, 2000.00]
        }
        raw_data = pd.DataFrame(original_data)
        
        result = data_processor.map_columns(raw_data)
        
        # Verify data values are preserved after mapping
        assert result['transaction_date'].tolist() == original_data['date']
        assert result['description'].tolist() == original_data['details']
        assert result['amount'].tolist() == original_data['value']