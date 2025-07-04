"""
Basic functionality tests for DataProcessor.

Simple tests to verify the DataProcessor works with the actual API.
"""

import pytest
import pandas as pd
from core.processors.data_processor import DataProcessor


class TestBasicFunctionality:
    """Basic functionality test cases."""

    def test_dataprocessor_initialization(self):
        """Test that DataProcessor can be initialized."""
        processor = DataProcessor()
        assert processor is not None

    def test_process_dataframe_returns_tuple(self, data_processor, sample_chase_data):
        """Test that process_dataframe returns a tuple."""
        result = data_processor.process_dataframe(sample_chase_data)
        
        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        processed_df, processing_result = result
        assert isinstance(processed_df, pd.DataFrame)
        assert processing_result is not None

    def test_process_dataframe_basic_structure(self, data_processor, sample_chase_data):
        """Test basic structure of process_dataframe output."""
        processed_df, processing_result = data_processor.process_dataframe(sample_chase_data)
        
        # Basic DataFrame checks
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 3  # Same number of rows as input
        assert len(processed_df.columns) > 0  # Has some columns
        
        # Basic ProcessingResult checks
        assert hasattr(processing_result, 'success')
        assert hasattr(processing_result, 'processed_rows')
        assert processing_result.processed_rows == 3

    def test_process_empty_dataframe(self, data_processor):
        """Test processing empty DataFrame."""
        empty_df = pd.DataFrame()
        processed_df, processing_result = data_processor.process_dataframe(empty_df)
        
        assert isinstance(processed_df, pd.DataFrame)
        assert processing_result is not None
        assert processing_result.processed_rows == 0

    def test_process_dataframe_preserves_data(self, data_processor, sample_chase_data):
        """Test that processing preserves the original data structure."""
        original_rows = len(sample_chase_data)
        processed_df, processing_result = data_processor.process_dataframe(sample_chase_data)
        
        # Should have same number of rows (or explain why not)
        assert len(processed_df) <= original_rows  # Could be less due to filtering
        assert processing_result.processed_rows == original_rows