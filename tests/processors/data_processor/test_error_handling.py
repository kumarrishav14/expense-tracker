"""
Error handling tests for DataProcessor.

Tests robust error handling and edge cases.
"""

import pandas as pd
import pytest


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_dataframe_error(self, data_processor, empty_dataframe):
        """Test proper error handling for empty DataFrame input."""
        with pytest.raises(ValueError, match="Input DataFrame is empty"):
            data_processor.process_raw_data(empty_dataframe)
    
    def test_no_mappable_columns_error(self, data_processor, no_mappable_columns_data):
        """Test error when no required columns can be mapped."""
        with pytest.raises(ValueError, match="Cannot map required columns"):
            data_processor.process_raw_data(no_mappable_columns_data)
    
    def test_missing_amount_column_error(self, data_processor):
        """Test error when amount column cannot be mapped."""
        invalid_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Test Transaction']
            # Missing any amount-related columns
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns.*amount"):
            data_processor.process_raw_data(invalid_data)
    
    def test_missing_date_column_error(self, data_processor):
        """Test error when date column cannot be mapped."""
        invalid_data = pd.DataFrame({
            'description': ['Test Transaction'],
            'amount': [1000.00]
            # Missing any date-related columns
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns.*transaction_date"):
            data_processor.process_raw_data(invalid_data)
    
    def test_missing_description_column_error(self, data_processor):
        """Test error when description column cannot be mapped."""
        invalid_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'amount': [1000.00]
            # Missing any description-related columns
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns.*description"):
            data_processor.process_raw_data(invalid_data)
    
    def test_all_invalid_dates_error(self, data_processor):
        """Test error when all dates are invalid."""
        invalid_data = pd.DataFrame({
            'date': ['invalid_date', 'another_invalid', ''],
            'description': ['Trans 1', 'Trans 2', 'Trans 3'],
            'amount': [1000.00, 2000.00, 3000.00]
        })
        
        with pytest.raises(ValueError, match="All rows were removed during data cleaning"):
            data_processor.process_raw_data(invalid_data)
    
    def test_all_invalid_amounts_error(self, data_processor):
        """Test error when all amounts are invalid."""
        invalid_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'description': ['Trans 1', 'Trans 2'],
            'amount': ['not_a_number', 'also_invalid']
        })
        
        with pytest.raises(ValueError, match="All rows were removed during data cleaning"):
            data_processor.process_raw_data(invalid_data)
    
    def test_all_empty_descriptions_error(self, data_processor):
        """Test error when all descriptions are empty."""
        invalid_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'description': ['', '   '],
            'amount': [1000.00, 2000.00]
        })
        
        with pytest.raises(ValueError, match="All rows were removed during data cleaning"):
            data_processor.process_raw_data(invalid_data)
    
    def test_completely_corrupted_data_error(self, data_processor):
        """Test handling of completely corrupted data."""
        corrupted_data = pd.DataFrame({
            'random_col1': [None, None, None],
            'random_col2': ['', '', ''],
            'random_col3': [0, 0, 0]
        })
        
        with pytest.raises(ValueError, match="Cannot map required columns"):
            data_processor.process_raw_data(corrupted_data)
    
    def test_date_parsing_failure_error(self, data_processor):
        """Test error handling when date parsing completely fails."""
        # Create data where date column exists but all values are unparseable
        invalid_data = pd.DataFrame({
            'transaction_date': ['not_a_date', 'invalid', 'bad_date'],
            'description': ['Trans 1', 'Trans 2', 'Trans 3'],
            'amount': [1000.00, 2000.00, 3000.00]
        })
        
        with pytest.raises(ValueError, match="All rows were removed during data cleaning"):
            data_processor.process_raw_data(invalid_data)
    
    def test_amount_parsing_failure_error(self, data_processor):
        """Test error handling when amount parsing completely fails."""
        invalid_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'description': ['Trans 1', 'Trans 2'],
            'amount': ['definitely_not_a_number', 'also_not_a_number']
        })
        
        with pytest.raises(ValueError, match="All rows were removed during data cleaning"):
            data_processor.process_raw_data(invalid_data)
    
    def test_mixed_valid_invalid_partial_processing(self, data_processor):
        """Test partial processing continues when some data is valid."""
        mixed_data = pd.DataFrame({
            'date': ['2024-01-15', 'invalid_date', '2024-01-17'],
            'description': ['Valid Trans', 'Invalid Date', 'Another Valid'],
            'amount': [1000.00, 2000.00, 3000.00]
        })
        
        # Should not raise error, should process valid rows
        result = data_processor.process_raw_data(mixed_data)
        
        # Verify partial processing worked
        assert len(result) >= 1
        assert len(result) < len(mixed_data)
        assert 'Valid Trans' in result['description'].values or 'Another Valid' in result['description'].values
    
    def test_single_valid_row_processing(self, data_processor):
        """Test processing when only one row is valid."""
        mostly_invalid_data = pd.DataFrame({
            'date': ['2024-01-15', 'invalid_date', 'another_invalid'],
            'description': ['Only Valid Transaction', '', 'Invalid Empty'],
            'amount': [1000.00, 'not_a_number', 'also_invalid']
        })
        
        result = data_processor.process_raw_data(mostly_invalid_data)
        
        # Should process the one valid row
        assert len(result) == 1
        assert result['description'].iloc[0] == 'Only Valid Transaction'
        assert result['amount'].iloc[0] == 1000.00
    
    def test_null_values_handling(self, data_processor):
        """Test handling of null values in data."""
        null_data = pd.DataFrame({
            'date': ['2024-01-15', None, '2024-01-17'],
            'description': ['Valid Trans', None, 'Another Valid'],
            'amount': [1000.00, None, 3000.00]
        })
        
        # Should process valid rows and skip null rows
        result = data_processor.process_raw_data(null_data)
        
        assert len(result) >= 1
        assert 'Valid Trans' in result['description'].values or 'Another Valid' in result['description'].values
    
    def test_extremely_large_amounts(self, data_processor):
        """Test handling of extremely large amounts."""
        large_amount_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Extremely Large Transaction'],
            'amount': [999999999999.99]  # Very large amount
        })
        
        # Should process successfully (no upper limit validation)
        result = data_processor.process_raw_data(large_amount_data)
        
        assert len(result) == 1
        assert result['amount'].iloc[0] == 999999999999.99
        # TODO: Enable when AI backend is available - assert result['sub_category'].iloc[0] == 'Large Transaction'
    
    def test_extremely_small_amounts(self, data_processor):
        """Test handling of extremely small amounts."""
        small_amount_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Extremely Small Transaction'],
            'amount': [0.001]  # Very small amount
        })
        
        # Should process successfully
        result = data_processor.process_raw_data(small_amount_data)
        
        assert len(result) == 1
        assert result['amount'].iloc[0] == 0.001
        # TODO: Enable when AI backend is available - assert result['sub_category'].iloc[0] == 'Small Transaction'
    
    def test_special_characters_in_descriptions(self, data_processor):
        """Test handling of special characters in descriptions."""
        special_char_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Transaction with special chars: @#$%^&*()'],
            'amount': [1000.00]
        })
        
        # Should process successfully
        result = data_processor.process_raw_data(special_char_data)
        
        assert len(result) == 1
        assert 'special chars' in result['description'].iloc[0]
    
    def test_unicode_characters_in_descriptions(self, data_processor):
        """Test handling of unicode characters in descriptions."""
        unicode_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Transaction with unicode: café résumé naïve'],
            'amount': [1000.00]
        })
        
        # Should process successfully
        result = data_processor.process_raw_data(unicode_data)
        
        assert len(result) == 1
        assert 'café' in result['description'].iloc[0]
    
    def test_very_long_descriptions(self, data_processor):
        """Test handling of very long descriptions."""
        long_description = 'A' * 1000  # Very long description
        long_desc_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': [long_description],
            'amount': [1000.00]
        })
        
        # Should process successfully
        result = data_processor.process_raw_data(long_desc_data)
        
        assert len(result) == 1
        assert len(result['description'].iloc[0]) == 1000
    
    def test_future_dates_handling(self, data_processor):
        """Test handling of future dates."""
        future_date_data = pd.DataFrame({
            'date': ['2030-01-15'],  # Future date
            'description': ['Future Transaction'],
            'amount': [1000.00]
        })
        
        # Should process successfully (no date range validation)
        result = data_processor.process_raw_data(future_date_data)
        
        assert len(result) == 1
        assert result['description'].iloc[0] == 'Future Transaction'
    
    def test_very_old_dates_handling(self, data_processor):
        """Test handling of very old dates."""
        old_date_data = pd.DataFrame({
            'date': ['1990-01-15'],  # Very old date
            'description': ['Old Transaction'],
            'amount': [1000.00]
        })
        
        # Should process successfully (no date range validation)
        result = data_processor.process_raw_data(old_date_data)
        
        assert len(result) == 1
        assert result['description'].iloc[0] == 'Old Transaction'
    
    def test_error_message_clarity(self, data_processor):
        """Test that error messages are clear and helpful."""
        invalid_data = pd.DataFrame({
            'random_column': ['data'],
            'another_column': ['more_data']
        })
        
        with pytest.raises(ValueError) as exc_info:
            data_processor.process_raw_data(invalid_data)
        
        error_message = str(exc_info.value)
        
        # Verify error message contains helpful information
        assert "Cannot map required columns" in error_message
        assert "Available columns" in error_message
        assert "random_column" in error_message or "another_column" in error_message
    
    def test_processing_doesnt_modify_input_data(self, data_processor):
        """Test that processing doesn't modify the original input DataFrame."""
        original_data = pd.DataFrame({
            'date': ['2024-01-15'],
            'description': ['Test Transaction'],
            'amount': [1000.00]
        })
        
        # Create a copy to compare against
        original_copy = original_data.copy()
        
        # Process the data
        result = data_processor.process_raw_data(original_data)
        
        # Verify original data wasn't modified
        pd.testing.assert_frame_equal(original_data, original_copy)
        
        # Verify result is different from input
        assert not original_data.equals(result)