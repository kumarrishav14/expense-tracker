"""
Basic functionality tests for DataProcessor.

Tests core functionality and happy path scenarios following the test plan.
"""

import pandas as pd
import pytest
from datetime import datetime


class TestBasicFunctionality:
    """Test basic DataProcessor functionality and happy path scenarios."""
    
    def test_process_standard_bank_statement(self, data_processor, standard_raw_data):
        """Test successful processing of well-formed standard bank statement."""
        result = data_processor.process_raw_data(standard_raw_data)
        
        # Verify output schema matches db_interface expectations
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(result.columns) == expected_columns
        
        # Verify data types
        assert result['amount'].dtype in ['float64', 'int64']
        assert pd.api.types.is_datetime64_any_dtype(result['transaction_date'])
        assert result['description'].dtype == 'object'
        
        # Verify all rows processed successfully
        assert len(result) == len(standard_raw_data)
        
        # Verify no null values in required fields
        assert not result['amount'].isnull().any()
        assert not result['transaction_date'].isnull().any()
        assert not result['description'].isnull().any()
    
    def test_processing_summary_generation(self, data_processor, standard_raw_data):
        """Test accurate processing summary generation."""
        processed_df = data_processor.process_raw_data(standard_raw_data)
        summary = data_processor.get_processing_summary(standard_raw_data, processed_df)
        
        # Verify summary structure
        required_keys = ['original_rows', 'processed_rows', 'rows_removed', 'categories_assigned', 'processing_success']
        for key in required_keys:
            assert key in summary
        
        # Verify summary accuracy
        assert summary['original_rows'] == len(standard_raw_data)
        assert summary['processed_rows'] == len(processed_df)
        assert summary['rows_removed'] == len(standard_raw_data) - len(processed_df)
        assert summary['processing_success'] is True
        
        # Verify categories were assigned
        categories_with_values = len(processed_df[processed_df['category'].notna()])
        assert summary['categories_assigned'] == categories_with_values
    
    def test_column_preservation(self, data_processor, standard_raw_data):
        """Test that only db_interface columns are preserved in final output."""
        # Add extra columns to input data
        input_data = standard_raw_data.copy()
        input_data['extra_column1'] = ['extra1', 'extra2', 'extra3']
        input_data['extra_column2'] = [100, 200, 300]
        
        result = data_processor.process_raw_data(input_data)
        
        # Verify only expected columns remain
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(result.columns) == expected_columns
        
        # Verify extra columns were removed
        assert 'extra_column1' not in result.columns
        assert 'extra_column2' not in result.columns
    
    def test_data_type_consistency(self, data_processor, variant_column_names_data):
        """Test proper data types in output DataFrame."""
        result = data_processor.process_raw_data(variant_column_names_data)
        
        # Verify specific data types
        assert result['amount'].dtype in ['float64', 'int64'], "Amount should be numeric"
        assert pd.api.types.is_datetime64_any_dtype(result['transaction_date']), "Date should be datetime"
        assert result['description'].dtype == 'object', "Description should be string"
        assert result['category'].dtype == 'object', "Category should be string"
        assert result['sub_category'].dtype == 'object', "Sub-category should be string"
        
        # Verify no mixed types within columns
        for col in result.columns:
            if col == 'amount':
                assert all(isinstance(val, (int, float)) for val in result[col])
            elif col == 'transaction_date':
                assert all(isinstance(val, pd.Timestamp) for val in result[col])
    
    def test_variant_column_names_processing(self, data_processor, variant_column_names_data):
        """Test processing of bank statement with variant column naming."""
        result = data_processor.process_raw_data(variant_column_names_data)
        
        # Verify successful mapping and processing
        assert len(result) == len(variant_column_names_data)
        
        # Verify data was correctly mapped
        assert 'Swiggy Food Order' in result['description'].values
        assert 450.75 in result['amount'].values
        
        # TODO: Enable when AI backend is available - Verify categories were assigned based on descriptions
        # swiggy_row = result[result['description'] == 'Swiggy Food Order']
        # assert len(swiggy_row) == 1
        # assert swiggy_row.iloc[0]['category'] == 'Food & Dining'
    
    def test_debit_credit_combination(self, data_processor, debit_credit_format_data):
        """Test proper combination of separate debit and credit columns."""
        result = data_processor.process_raw_data(debit_credit_format_data)
        
        # Verify amounts are correctly combined
        expected_amounts = [-750.00, 45000.00, -1000.00]  # debit negative, credit positive
        actual_amounts = result['amount'].tolist()
        
        for expected, actual in zip(expected_amounts, actual_amounts):
            assert abs(expected - actual) < 0.01, f"Expected {expected}, got {actual}"
        
        # Verify all transactions processed
        assert len(result) == len(debit_credit_format_data)
    
    def test_empty_optional_fields_handling(self, data_processor):
        """Test handling of data with missing optional fields."""
        # Create data with only required fields
        minimal_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'description': ['Transaction 1', 'Transaction 2'],
            'amount': [1000.00, 2000.00]
        })
        
        result = data_processor.process_raw_data(minimal_data)
        
        # Verify optional fields are added with appropriate defaults
        assert 'category' in result.columns
        assert 'sub_category' in result.columns
        
        # TODO: Enable when AI backend is available - Verify categories were assigned by AI logic
        # assert not result['category'].isnull().all()  # At least some should be assigned
        # assert not result['sub_category'].isnull().all()  # Sub-categories based on amount
    
    def test_processing_preserves_transaction_order(self, data_processor, standard_raw_data):
        """Test that transaction order is preserved during processing."""
        result = data_processor.process_raw_data(standard_raw_data)
        
        # Verify order is preserved (assuming no duplicates removed)
        original_descriptions = standard_raw_data['description'].tolist()
        result_descriptions = result['description'].tolist()
        
        assert original_descriptions == result_descriptions
    
    def test_large_dataset_processing(self, data_processor, large_dataset):
        """Test processing of larger dataset for basic performance validation."""
        result = data_processor.process_raw_data(large_dataset)
        
        # Verify all data processed successfully
        assert len(result) > 0
        assert len(result) <= len(large_dataset)  # May be less due to cleaning
        
        # Verify schema consistency
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(result.columns) == expected_columns
        
        # TODO: Enable when AI backend is available - Verify categories were assigned
        # assert not result['category'].isnull().all()
    
    def test_processor_initialization(self, data_processor):
        """Test DataProcessor initializes with correct configuration."""
        # Verify column mappings are configured
        assert hasattr(data_processor, 'column_mappings')
        assert 'transaction_date' in data_processor.column_mappings
        assert 'amount' in data_processor.column_mappings
        assert 'description' in data_processor.column_mappings
        
        # Verify category rules are configured
        assert hasattr(data_processor, 'category_rules')
        assert 'Food & Dining' in data_processor.category_rules
        assert 'Transportation' in data_processor.category_rules
        
        # Verify db_interface columns are defined
        assert hasattr(data_processor, 'db_interface_columns')
        expected_db_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert data_processor.db_interface_columns == expected_db_columns