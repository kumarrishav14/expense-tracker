"""
Integration tests for DataProcessor.

Tests complete processing pipeline end-to-end.
"""

import pandas as pd
import pytest


class TestIntegration:
    """Test complete DataProcessor pipeline integration."""
    
    def test_complete_processing_pipeline(self, data_processor, standard_raw_data):
        """Test complete pipeline from raw data to standardized output."""
        result = data_processor.process_raw_data(standard_raw_data)
        
        # Verify output schema matches db_interface expectations
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(result.columns) == expected_columns
        
        # Verify data types
        assert result['amount'].dtype in ['float64', 'int64']
        assert pd.api.types.is_datetime64_any_dtype(result['transaction_date'])
        assert result['description'].dtype == 'object'
        
        # Verify all rows processed
        assert len(result) == len(standard_raw_data)
        
        # TODO: Enable when AI backend is available - Verify categories were assigned
        # assert not result['category'].isnull().all()
        # assert not result['sub_category'].isnull().all()
    
    def test_variant_format_end_to_end(self, data_processor, variant_column_names_data):
        """Test end-to-end processing of variant column format."""
        result = data_processor.process_raw_data(variant_column_names_data)
        
        # Verify successful processing
        assert len(result) == len(variant_column_names_data)
        
        # Verify specific data transformations
        assert 'Swiggy Food Order' in result['description'].values
        assert 450.75 in result['amount'].values
        
        # TODO: Enable when AI backend is available - Verify categorization worked
        # swiggy_row = result[result['description'] == 'Swiggy Food Order']
        # assert swiggy_row.iloc[0]['category'] == 'Food & Dining'
    
    def test_debit_credit_format_end_to_end(self, data_processor, debit_credit_format_data):
        """Test end-to-end processing of debit/credit format."""
        result = data_processor.process_raw_data(debit_credit_format_data)
        
        # Verify debit/credit combination
        expected_amounts = [-750.00, 45000.00, -1000.00]
        actual_amounts = result['amount'].tolist()
        
        for expected, actual in zip(expected_amounts, actual_amounts):
            assert abs(expected - actual) < 0.01
        
        # TODO: Enable when AI backend is available - Verify categorization based on descriptions
        # salary_row = result[result['description'] == 'Salary']
        # assert salary_row.iloc[0]['category'] == 'Salary'
        # assert salary_row.iloc[0]['sub_category'] == 'Large Transaction'
    
    def test_messy_data_partial_processing(self, data_processor, messy_data):
        """Test partial processing when some rows are invalid."""
        result = data_processor.process_raw_data(messy_data)
        
        # Should process valid rows and skip invalid ones
        assert len(result) >= 1  # At least some valid data should remain
        assert len(result) < len(messy_data)  # Some invalid data should be removed
        
        # Verify valid data was processed correctly
        if len(result) > 0:
            assert 'Valid Transaction' in result['description'].values or 'Another Valid' in result['description'].values
    
    def test_large_dataset_processing(self, data_processor, large_dataset):
        """Test processing of larger dataset."""
        result = data_processor.process_raw_data(large_dataset)
        
        # Verify successful processing
        assert len(result) > 0
        assert len(result) <= len(large_dataset)
        
        # Verify schema consistency
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(result.columns) == expected_columns
        
        # TODO: Enable when AI backend is available - Verify categories were assigned across the dataset
        # category_counts = result['category'].value_counts()
        # assert len(category_counts) > 1  # Multiple categories should be assigned
    
    def test_currency_symbols_processing(self, data_processor, currency_symbols_data):
        """Test processing of data with various currency symbols."""
        result = data_processor.process_raw_data(currency_symbols_data)
        
        # Verify currency symbols were cleaned
        assert result['amount'].dtype in ['float64', 'int64']
        
        # Verify specific amount conversions
        amounts = result['amount'].tolist()
        assert 1500.50 in amounts
        assert 2000.00 in amounts
        assert 150.75 in amounts
    
    def test_duplicate_removal_integration(self, data_processor, duplicate_transactions_data):
        """Test duplicate removal in complete pipeline."""
        result = data_processor.process_raw_data(duplicate_transactions_data)
        
        # Verify duplicates were removed
        assert len(result) == 2  # Should have 2 unique transactions
        
        # Verify unique transactions remain
        descriptions = result['description'].tolist()
        assert 'Amazon Purchase' in descriptions
        assert 'Different Purchase' in descriptions
        assert descriptions.count('Amazon Purchase') == 1  # Only one instance
    
    def test_edge_case_amounts_processing(self, data_processor, edge_case_amounts):
        """Test processing of edge case amounts."""
        result = data_processor.process_raw_data(edge_case_amounts)
        
        # Verify all amounts processed (including zero)
        assert len(result) == len(edge_case_amounts)
        
        # TODO: Enable when AI backend is available - Verify sub-category assignment for edge cases
        # small_amount_row = result[result['amount'] == 0.01]
        # large_amount_row = result[result['amount'] == 100000.00]
        # assert small_amount_row.iloc[0]['sub_category'] == 'Small Transaction'
        # assert large_amount_row.iloc[0]['sub_category'] == 'Large Transaction'
    
    def test_processing_summary_integration(self, data_processor, messy_data):
        """Test processing summary with mixed valid/invalid data."""
        processed_df = data_processor.process_raw_data(messy_data)
        summary = data_processor.get_processing_summary(messy_data, processed_df)
        
        # Verify summary accuracy
        assert summary['original_rows'] == len(messy_data)
        assert summary['processed_rows'] == len(processed_df)
        assert summary['rows_removed'] == len(messy_data) - len(processed_df)
        assert summary['processing_success'] is True
        
        # Verify categories assigned count
        categories_assigned = len(processed_df[processed_df['category'].notna()])
        assert summary['categories_assigned'] == categories_assigned
    
    def test_real_bank_statement_format_1(self, data_processor):
        """Test processing of realistic bank statement format 1."""
        bank_data = pd.DataFrame({
            'Transaction Date': ['15-Jan-2024', '16-Jan-2024', '17-Jan-2024'],
            'Transaction Details': [
                'UPI-AMAZON PAY INDIA PVT LTD-AMAZON-123456789@paytm',
                'SALARY CREDIT FROM XYZ COMPANY LTD',
                'ATM WDL TXN FEE 123456XXXXXX1234 HDFC BANK ATM'
            ],
            'Debit': [1299.00, None, 2500.00],
            'Credit': [None, 75000.00, None],
            'Balance': [45000.00, 120000.00, 117500.00]
        })
        
        result = data_processor.process_raw_data(bank_data)
        
        # Verify successful processing
        assert len(result) == 3
        
        # Verify amount calculations
        assert -1299.00 in result['amount'].values  # Debit as negative
        assert 75000.00 in result['amount'].values  # Credit as positive
        assert -2500.00 in result['amount'].values  # ATM fee as negative
        
        # TODO: Enable when AI backend is available - Verify categorization
        # amazon_row = result[result['description'].str.contains('AMAZON', case=False)]
        # salary_row = result[result['description'].str.contains('SALARY', case=False)]
        # atm_row = result[result['description'].str.contains('ATM', case=False)]
        # assert len(amazon_row) == 1 and amazon_row.iloc[0]['category'] == 'Shopping'
        # assert len(salary_row) == 1 and salary_row.iloc[0]['category'] == 'Salary'
        # assert len(atm_row) == 1 and atm_row.iloc[0]['category'] == 'ATM'
    
    def test_real_bank_statement_format_2(self, data_processor):
        """Test processing of realistic bank statement format 2."""
        bank_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'narration': [
                'SWIGGY INSTANT FOOD DELIVERY',
                'NEFT CR-HDFC0000123-JOHN DOE-RENT PAYMENT',
                'POS 123456XXXXXX1234 BIG BAZAAR MUMBAI'
            ],
            'amount': ['Rs 450.75', 'Rs 25,000.00', 'Rs 2,150.50'],
            'type': ['DEBIT', 'CREDIT', 'DEBIT']
        })
        
        result = data_processor.process_raw_data(bank_data)
        
        # Verify successful processing
        assert len(result) == 3
        
        # Verify currency cleaning worked
        assert 450.75 in result['amount'].values
        assert 25000.00 in result['amount'].values
        assert 2150.50 in result['amount'].values
        
        # TODO: Enable when AI backend is available - Verify categorization
        # swiggy_row = result[result['description'].str.contains('SWIGGY', case=False)]
        # transfer_row = result[result['description'].str.contains('NEFT', case=False)]
        # shopping_row = result[result['description'].str.contains('BAZAAR', case=False)]
        # assert len(swiggy_row) == 1 and swiggy_row.iloc[0]['category'] == 'Food & Dining'
        # assert len(transfer_row) == 1 and transfer_row.iloc[0]['category'] == 'Transfer'
        # assert len(shopping_row) == 1 and shopping_row.iloc[0]['category'] == 'Shopping'
    
    def test_minimal_required_columns_processing(self, data_processor):
        """Test processing with only minimal required columns."""
        minimal_data = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'description': ['Minimal Transaction 1', 'Minimal Transaction 2'],
            'amount': [1000.00, 2000.00]
        })
        
        result = data_processor.process_raw_data(minimal_data)
        
        # Verify successful processing
        assert len(result) == 2
        
        # Verify all required columns present
        expected_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
        assert list(result.columns) == expected_columns
        
        # TODO: Enable when AI backend is available - Verify optional columns were populated
        # assert not result['category'].isnull().all()
        # assert not result['sub_category'].isnull().all()
    
    def test_error_recovery_partial_processing(self, data_processor):
        """Test error recovery when some data is processable."""
        mixed_data = pd.DataFrame({
            'transaction_date': ['2024-01-15', 'invalid_date', '2024-01-17'],
            'description': ['Valid Transaction', 'Invalid Date Row', 'Another Valid'],
            'amount': [1000.00, 'invalid_amount', 3000.00]
        })
        
        result = data_processor.process_raw_data(mixed_data)
        
        # Should process valid rows despite some invalid data
        assert len(result) >= 1
        
        # Verify valid data was processed
        valid_descriptions = ['Valid Transaction', 'Another Valid']
        processed_descriptions = result['description'].tolist()
        
        # At least one valid transaction should be processed
        assert any(desc in processed_descriptions for desc in valid_descriptions)