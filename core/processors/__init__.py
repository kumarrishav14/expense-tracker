"""
Data Processor Module

This module provides data transformation and validation capabilities for converting
raw parsed bank statement data into standardized pandas DataFrames compatible with
the database interface.

Components:
- DataProcessor: Main processing orchestrator
- ColumnMapper: Intelligent column mapping engine
- DataValidator: Data validation and quality checks
- CategoryPredictor: AI-powered transaction categorization
- DataCleaner: Data cleaning and standardization

Author: Rovo Dev
Created: 2025-01-02
"""

from .data_processor import DataProcessor
from .exceptions import (
    DataProcessorError,
    ColumnMappingError,
    ValidationError,
    CategoryPredictionError,
)
from .schemas import (
    ProcessingConfig,
    ColumnMappingRule,
    ValidationResult,
    ProcessingResult,
    ErrorReport,
    ColumnType,
    ProcessingMode,
    ValidationSeverity,
)

__all__ = [
    "DataProcessor",
    "DataProcessorError",
    "ColumnMappingError", 
    "ValidationError",
    "CategoryPredictionError",
    "ProcessingConfig",
    "ColumnMappingRule",
    "ValidationResult",
    "ProcessingResult",
    "ErrorReport",
    "ColumnType",
    "ProcessingMode",
    "ValidationSeverity",
]