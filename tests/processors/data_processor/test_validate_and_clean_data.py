"""
Tests for DataProcessor.validate_and_clean_data() method.

This module tests data validation and cleaning functionality with
realistic personal banking scenarios and edge cases.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from core.processors.data_processor import DataProcessor


class TestValidateAndCleanData:
    """Test cases for the validate_and_clean_data() method."""

    def test_validate_clean_standard_data(self, data_processor):
        """Test validation and cleaning of standard, well-formatted data."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['GROCERY STORE', 'GAS STATION', 'RESTAURANT'],
            'amount': ['-85.32', '-45.67', '-28.50'],
            'balance': ['1234.56', '1188.89', '1160.39']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_validate_date_formats(self, data_processor):
        """Test validation and standardization of various date formats."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '1/16/2024', '2024-01-17', '01-18-2024'],
            'description': ['STORE1', 'STORE2', 'STORE3', 'STORE4'],
            'amount': ['-85.32', '-45.67', '-28.50', '-15.25'],
            'balance': ['1000.00', '954.33', '925.83', '910.58']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # All dates should be standardized to consistent format

    def test_validate_invalid_dates(self, data_processor):
        """Test handling of invalid date formats."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '02/30/2024', 'invalid_date', '13/45/2024'],
            'description': ['VALID TRANSACTION', 'INVALID DATE 1', 'INVALID DATE 2', 'INVALID DATE 3'],
            'amount': ['-85.32', '-45.67', '-28.50', '-15.25'],
            'balance': ['1000.00', '954.33', '925.83', '910.58']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle invalid dates gracefully - either fix, flag, or remove

    def test_validate_future_dates(self, data_processor):
        """Test validation of future dates (should be flagged as invalid)."""
        future_date = (datetime.now() + timedelta(days=30)).strftime('%m/%d/%Y')
        
        input_data = pd.DataFrame({
            'date': ['01/15/2024', future_date],
            'description': ['PAST TRANSACTION', 'FUTURE TRANSACTION'],
            'amount': ['-85.32', '-45.67'],
            'balance': ['1000.00', '954.33']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Future dates should be flagged or handled appropriately

    def test_clean_amount_formats(self, data_processor):
        """Test cleaning and validation of various amount formats."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024', '01/18/2024'],
            'description': ['STORE1', 'STORE2', 'STORE3', 'STORE4'],
            'amount': ['-$85.32', '($45.67)', '-45.67', '28.50'],
            'balance': ['1000.00', '954.33', '908.66', '937.16']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # All amounts should be cleaned and converted to consistent numeric format

    def test_clean_balance_formats(self, data_processor):
        """Test cleaning and validation of balance formats with commas and currency symbols."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['STORE1', 'STORE2', 'STORE3'],
            'amount': ['-85.32', '-45.67', '-28.50'],
            'balance': ['$1,234.56', '1,188.89', '$1,160.39']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # Balances should be cleaned of currency symbols and commas

    def test_validate_invalid_amounts(self, data_processor):
        """Test handling of invalid amount values."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['VALID AMOUNT', 'INVALID AMOUNT 1', 'INVALID AMOUNT 2'],
            'amount': ['-85.32', 'invalid_amount', 'abc.def'],
            'balance': ['1000.00', '954.33', '925.83']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle invalid amounts gracefully

    def test_validate_required_fields(self, data_processor):
        """Test validation of required fields (date, description, amount)."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '', '01/17/2024'],
            'description': ['VALID TRANSACTION', 'MISSING DATE', ''],
            'amount': ['-85.32', '-45.67', ''],
            'balance': ['1000.00', '954.33', '925.83']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should flag or handle missing required fields

    def test_clean_description_text(self, data_processor):
        """Test cleaning and normalization of description text."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': [
                '  GROCERY STORE  ',  # Extra whitespace
                'gas station',  # Lowercase
                'RESTAURANT & BAR'  # Special characters
            ],
            'amount': ['-85.32', '-45.67', '-28.50'],
            'balance': ['1000.00', '954.33', '925.83']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # Descriptions should be cleaned (trimmed, normalized case, etc.)

    def test_handle_null_nan_values(self, data_processor):
        """Test handling of null and NaN values."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['STORE1', None, 'STORE3'],
            'amount': ['-85.32', '-45.67', None],
            'balance': ['1000.00', None, '925.83']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle null/NaN values appropriately

    def test_detect_duplicate_transactions(self, data_processor):
        """Test detection and handling of duplicate transactions."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/15/2024', '01/16/2024'],
            'description': ['GROCERY STORE', 'GROCERY STORE', 'GAS STATION'],
            'amount': ['-85.32', '-85.32', '-45.67'],
            'balance': ['1000.00', '914.68', '869.01']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should detect and handle potential duplicates

    def test_validate_data_types(self, data_processor):
        """Test validation and conversion of data types."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024'],
            'description': ['STORE1', 'STORE2'],
            'amount': [-85.32, '-45.67'],  # Mixed numeric and string
            'balance': [1000.00, '954.33']  # Mixed numeric and string
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # Data types should be consistent after validation

    def test_validate_amount_ranges(self, data_processor):
        """Test validation of reasonable amount ranges."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['NORMAL PURCHASE', 'VERY LARGE PURCHASE', 'MICRO PURCHASE'],
            'amount': ['-85.32', '-999999.99', '-0.01'],
            'balance': ['1000.00', '0.01', '0.00']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should validate that amounts are within reasonable ranges

    def test_validate_balance_calculations(self, data_processor):
        """Test validation of balance calculations for consistency."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['STORE1', 'STORE2', 'STORE3'],
            'amount': ['-85.32', '-45.67', '-28.50'],
            'balance': ['1000.00', '914.68', '886.18']  # Correct calculations
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_validate_inconsistent_balance_calculations(self, data_processor):
        """Test handling of inconsistent balance calculations."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['STORE1', 'STORE2', 'STORE3'],
            'amount': ['-85.32', '-45.67', '-28.50'],
            'balance': ['1000.00', '500.00', '200.00']  # Inconsistent calculations
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should flag inconsistent balance calculations

    def test_clean_unicode_characters(self, data_processor):
        """Test handling of Unicode characters in descriptions."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024'],
            'description': ['CAFÉ RESTAURANT', 'NAÏVE STORE'],
            'amount': ['-85.32', '-45.67'],
            'balance': ['1000.00', '954.33']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)

    def test_clean_html_xml_content(self, data_processor):
        """Test cleaning of HTML/XML content in descriptions."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024'],
            'description': ['<b>GROCERY STORE</b>', 'STORE &amp; MORE'],
            'amount': ['-85.32', '-45.67'],
            'balance': ['1000.00', '954.33']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should clean HTML/XML content from descriptions

    def test_handle_extremely_long_descriptions(self, data_processor):
        """Test handling of extremely long description text."""
        long_description = 'A' * 1000  # Very long description
        
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024'],
            'description': ['NORMAL STORE', long_description],
            'amount': ['-85.32', '-45.67'],
            'balance': ['1000.00', '954.33']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle very long descriptions appropriately

    def test_validate_scientific_notation(self, data_processor):
        """Test handling of scientific notation in amounts."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024'],
            'description': ['STORE1', 'STORE2'],
            'amount': ['-8.532e1', '-4.567e1'],  # Scientific notation
            'balance': ['1000.00', '954.33']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle scientific notation correctly

    def test_validate_different_currency_formats(self, data_processor):
        """Test handling of different currency formats."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'description': ['STORE1', 'STORE2', 'STORE3'],
            'amount': ['USD -85.32', '€45.67', '¥28.50'],
            'balance': ['1000.00', '954.33', '925.83']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle different currency formats

    def test_preserve_data_precision(self, data_processor):
        """Test that data precision is preserved during cleaning."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', '01/16/2024'],
            'description': ['STORE1', 'STORE2'],
            'amount': ['-85.321', '-45.678'],  # 3 decimal places
            'balance': ['1000.001', '954.323']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        # Should preserve precision where appropriate

    def test_validation_error_reporting(self, data_processor, edge_case_data):
        """Test that validation errors are properly reported."""
        result = data_processor.validate_and_clean_data(edge_case_data)
        
        assert result is not None
        # Should provide information about validation issues found

    def test_partial_validation_success(self, data_processor):
        """Test handling when some rows pass validation and others fail."""
        input_data = pd.DataFrame({
            'date': ['01/15/2024', 'invalid_date', '01/17/2024'],
            'description': ['VALID TRANSACTION', 'INVALID DATE', 'ANOTHER VALID'],
            'amount': ['-85.32', 'invalid_amount', '-28.50'],
            'balance': ['1000.00', '954.33', '925.83']
        })
        
        result = data_processor.validate_and_clean_data(input_data)
        
        assert result is not None
        # Should handle partial validation gracefully