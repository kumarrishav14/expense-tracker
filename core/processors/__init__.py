"""
Data Processors Package

Simplified data processing package for converting raw bank statement data 
into standardized DataFrames compatible with db_interface.

This package provides a single DataProcessor class that follows the approved
micro-architecture with 4 simple methods.

Usage:
    from core.processors import DataProcessor
    
    processor = DataProcessor()
    result = processor.process_raw_data(raw_df)
"""

from .data_processor import DataProcessor

__all__ = [
    'DataProcessor'
]