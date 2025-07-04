"""
Performance tests for DataProcessor component.

This module tests performance characteristics with realistic personal
banking data volumes and usage patterns.
"""

import pytest
import pandas as pd
import time
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
import os
from datetime import datetime, timedelta

from core.processors.data_processor import DataProcessor


class TestDataProcessorPerformance:
    """Performance test cases for DataProcessor."""

    def test_small_dataset_performance(self, data_processor):
        """Test performance with small dataset (50 transactions)."""
        small_data = pd.DataFrame({
            'Date': [f'01/{i:02d}/2024' for i in range(1, 51)],
            'Description': [f'TRANSACTION {i}' for i in range(1, 51)],
            'Amount': [f'-{10 + i}.50' for i in range(50)],
            'Balance': [f'{5000 - (10 + i) * i}' for i in range(50)]
        })
        
        start_time = time.time()
        processed_df, processing_result = data_processor.process_dataframe(small_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        # Should process 50 transactions very quickly
        assert processing_time < 1.0  # Less than 1 second

    def test_medium_dataset_performance(self, data_processor):
        """Test performance with medium dataset (200 transactions)."""
        medium_data = pd.DataFrame({
            'Date': [f'01/{(i % 31) + 1:02d}/2024' for i in range(200)],
            'Description': [f'TRANSACTION {i}' for i in range(200)],
            'Amount': [f'-{10 + (i % 100)}.50' for i in range(200)],
            'Balance': [f'{5000 - (10 + i) * (i % 10)}' for i in range(200)]
        })
        
        start_time = time.time()
        processed_df, processing_result = data_processor.process_dataframe(medium_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        # Should process 200 transactions quickly for personal app
        assert processing_time < 2.0  # Less than 2 seconds

    def test_large_dataset_performance(self, data_processor, large_dataset):
        """Test performance with large dataset (500 transactions)."""
        start_time = time.time()
        processed_df, processing_result = data_processor.process_dataframe(large_dataset)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        # Should process 500 transactions in reasonable time
        assert processing_time < 5.0  # Less than 5 seconds

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason='psutil not available')
    def test_memory_usage_small_dataset(self, data_processor):
        """Test memory usage with small dataset."""
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        small_data = pd.DataFrame({
            'Date': [f'01/{i:02d}/2024' for i in range(1, 51)],
            'Description': [f'TRANSACTION {i}' for i in range(1, 51)],
            'Amount': [f'-{10 + i}.50' for i in range(50)],
            'Balance': [f'{5000 - i * 10}' for i in range(50)]
        })
        
        processed_df, processing_result = data_processor.process_dataframe(small_data)
        
        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        assert processed_df is not None
        # Memory increase should be minimal for small datasets
        assert memory_increase < 10 * 1024 * 1024  # Less than 10MB

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason='psutil not available')
    def test_memory_usage_large_dataset(self, data_processor, large_dataset):
        """Test memory usage with large dataset."""
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
        
        processed_df, processing_result = data_processor.process_dataframe(large_dataset)
        
        memory_after = process.memory_info().rss
        memory_increase = memory_after - memory_before
        
        assert processed_df is not None
        # Memory increase should be reasonable for personal app
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB

    def test_repeated_processing_performance(self, data_processor, sample_chase_data):
        """Test performance with repeated processing of same data."""
        processing_times = []
        
        for i in range(10):
            start_time = time.time()
            processed_df, processing_result = data_processor.process_dataframe(sample_chase_data.copy())
            end_time = time.time()
            
            processing_times.append(end_time - start_time)
            assert processed_df is not None
        
        # Performance should be consistent across runs
        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 1.0  # Average should be under 1 second
        
        # No significant performance degradation
        assert max(processing_times) < 2 * min(processing_times)

    def test_concurrent_processing_performance(self, data_processor, sample_chase_data, sample_bofa_data):
        """Test performance with concurrent-like processing."""
        start_time = time.time()
        
        # Simulate concurrent processing by rapid sequential calls
        results = []
        for i in range(5):
            result1 = data_processor.process_dataframe(sample_chase_data.copy())
            result2 = data_processor.process_dataframe(sample_bofa_data.copy())
            results.extend([result1, result2])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All results should be valid
        for result in results:
            assert processed_df is not None
        
        # Should handle multiple rapid calls efficiently
        assert total_time < 10.0  # Less than 10 seconds for 10 calls

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason='psutil not available')
    def test_memory_cleanup_after_processing(self, data_processor):
        """Test that memory is properly cleaned up after processing."""
        import gc
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple datasets
        for i in range(5):
            large_data = pd.DataFrame({
                'Date': [f'01/{j:02d}/2024' for j in range(1, 101)],
                'Description': [f'TRANSACTION {j}' for j in range(100)],
                'Amount': [f'-{10 + j}.50' for j in range(100)],
                'Balance': [f'{5000 - j * 10}' for j in range(100)]
            })
            
            processed_df, processing_result = data_processor.process_dataframe(large_data)
            assert processed_df is not None
            
            # Clear references
            del large_data, result
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly after cleanup
        assert memory_increase < 20 * 1024 * 1024  # Less than 20MB permanent increase

    def test_processing_time_scalability(self, data_processor):
        """Test that processing time scales reasonably with data size."""
        sizes = [50, 100, 200, 400]
        times = []
        
        for size in sizes:
            data = pd.DataFrame({
                'Date': [f'01/{(i % 31) + 1:02d}/2024' for i in range(size)],
                'Description': [f'TRANSACTION {i}' for i in range(size)],
                'Amount': [f'-{10 + (i % 100)}.50' for i in range(size)],
                'Balance': [f'{5000 - i * 10}' for i in range(size)]
            })
            
            start_time = time.time()
            processed_df, processing_result = data_processor.process_dataframe(data)
            end_time = time.time()
            
            times.append(end_time - start_time)
            assert processed_df is not None
        
        # Processing time should scale reasonably (not exponentially)
        # Time for 400 records should not be more than 10x time for 50 records
        assert times[-1] < 10 * times[0]

    def test_column_mapping_performance(self, data_processor):
        """Test performance of column mapping with various formats."""
        formats = [
            {'Transaction Date': 'date', 'Description': 'desc', 'Amount': 'amt', 'Balance': 'bal'},
            {'Date': 'date', 'Desc': 'desc', 'Amt': 'amt', 'Bal': 'bal'},
            {'Txn Date': 'date', 'Txn Desc': 'desc', 'Txn Amt': 'amt', 'Account Bal': 'bal'},
        ]
        
        for format_dict in formats:
            data = pd.DataFrame({
                list(format_dict.keys())[0]: ['01/15/2024'] * 100,
                list(format_dict.keys())[1]: ['STORE'] * 100,
                list(format_dict.keys())[2]: ['-10.00'] * 100,
                list(format_dict.keys())[3]: ['1000.00'] * 100
            })
            
            start_time = time.time()
            result = data_processor.map_columns(data)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            assert processed_df is not None
            # Column mapping should be fast
            assert processing_time < 1.0

    def test_validation_performance(self, data_processor):
        """Test performance of data validation and cleaning."""
        # Create data with various validation challenges
        validation_data = pd.DataFrame({
            'date': ['01/15/2024', '1/16/2024', '2024-01-17'] * 100,
            'description': ['  STORE  ', 'gas station', 'RESTAURANT #123'] * 100,
            'amount': ['-$85.32', '($45.67)', '-1,234.56'] * 100,
            'balance': ['$1,234.56', '1,188.89', '$1,160.39'] * 100
        })
        
        start_time = time.time()
        result = data_processor.validate_and_clean_data(validation_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processed_df is not None
        # Validation should be reasonably fast even with cleaning tasks
        assert processing_time < 3.0

    def test_real_world_monthly_processing_performance(self, data_processor):
        """Test performance with realistic monthly personal banking data."""
        # Simulate a typical month of personal banking (80 transactions)
        base_date = datetime(2024, 1, 1)
        monthly_data = []
        
        transaction_types = [
            ('SALARY DEPOSIT', 2500.00),
            ('GROCERY STORE', -75.50),
            ('GAS STATION', -45.00),
            ('RESTAURANT', -35.25),
            ('COFFEE SHOP', -5.50),
            ('ONLINE PURCHASE', -125.75),
            ('UTILITY BILL', -85.30),
            ('PHONE BILL', -65.00),
            ('SUBSCRIPTION', -12.99),
            ('ATM WITHDRAWAL', -100.00)
        ]
        
        for i in range(80):
            date = base_date + timedelta(days=i // 3)
            desc, amount = transaction_types[i % len(transaction_types)]
            monthly_data.append({
                'Transaction Date': date.strftime('%m/%d/%Y'),
                'Description': f"{desc} {i+1}",
                'Amount': amount,
                'Balance': 5000 + sum([t[1] for t in transaction_types[:i+1]])
            })
        
        realistic_data = pd.DataFrame(monthly_data)
        
        start_time = time.time()
        processed_df, processing_result = data_processor.process_dataframe(realistic_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        # Should process monthly data very quickly for personal app
        assert processing_time < 2.0

    def test_performance_with_problematic_data(self, data_processor, edge_case_data):
        """Test performance when processing problematic/edge case data."""
        start_time = time.time()
        processed_df, processing_result = data_processor.process_dataframe(edge_case_data)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert processed_df is not None
        # Even problematic data should be processed in reasonable time
        assert processing_time < 5.0

    @pytest.mark.skipif(not PSUTIL_AVAILABLE, reason='psutil not available')
    def test_cpu_usage_during_processing(self, data_processor, large_dataset):
        """Test CPU usage during processing (basic monitoring)."""
        process = psutil.Process(os.getpid())
        
        # Get CPU usage before processing
        cpu_before = process.cpu_percent()
        
        processed_df, processing_result = data_processor.process_dataframe(large_dataset)
        
        # Get CPU usage after processing
        cpu_after = process.cpu_percent()
        
        assert processed_df is not None
        # CPU usage should be reasonable (this is a basic check)
        # Exact values depend on system, so we just ensure it doesn't hang
        assert cpu_after >= 0  # Basic sanity check