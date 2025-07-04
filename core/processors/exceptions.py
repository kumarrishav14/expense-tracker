"""
Custom exceptions for the data processor module.

This module defines all custom exceptions used throughout the data processing
pipeline to provide clear error handling and debugging information.
"""

from typing import Optional, Dict, Any


class DataProcessorError(Exception):
    """
    Base exception for all data processor related errors.
    
    This is the parent class for all custom exceptions in the data processor
    module, providing a common interface for error handling.
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the base data processor error.
        
        Args:
            message: Human-readable error message
            error_code: Optional error code for programmatic handling
            context: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        """Return formatted error message with context."""
        base_msg = self.message
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg = f"{base_msg} (Context: {context_str})"
        return base_msg


class ColumnMappingError(DataProcessorError):
    """
    Exception raised when column mapping fails.
    
    This exception is raised when the intelligent column mapping system
    cannot successfully map raw DataFrame columns to the standard schema.
    """
    
    def __init__(
        self,
        message: str,
        unmapped_columns: Optional[list] = None,
        missing_required_columns: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize column mapping error.
        
        Args:
            message: Error description
            unmapped_columns: List of columns that couldn't be mapped
            missing_required_columns: List of required columns not found
            **kwargs: Additional context passed to parent
        """
        context = kwargs.get('context', {})
        if unmapped_columns:
            context['unmapped_columns'] = unmapped_columns
        if missing_required_columns:
            context['missing_required_columns'] = missing_required_columns
        
        super().__init__(message, error_code="COLUMN_MAPPING_FAILED", context=context)
        self.unmapped_columns = unmapped_columns or []
        self.missing_required_columns = missing_required_columns or []


class ValidationError(DataProcessorError):
    """
    Exception raised when data validation fails.
    
    This exception is raised when the data validation engine detects
    data quality issues, business rule violations, or data consistency problems.
    """
    
    def __init__(
        self,
        message: str,
        validation_errors: Optional[list] = None,
        failed_rows: Optional[list] = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error description
            validation_errors: List of specific validation failures
            failed_rows: List of row indices that failed validation
            **kwargs: Additional context passed to parent
        """
        context = kwargs.get('context', {})
        if validation_errors:
            context['validation_errors'] = validation_errors
        if failed_rows:
            context['failed_rows'] = failed_rows
        
        super().__init__(message, error_code="VALIDATION_FAILED", context=context)
        self.validation_errors = validation_errors or []
        self.failed_rows = failed_rows or []


class CategoryPredictionError(DataProcessorError):
    """
    Exception raised when AI category prediction fails.
    
    This exception is raised when the AI-powered categorization system
    encounters errors during category prediction or confidence scoring.
    """
    
    def __init__(
        self,
        message: str,
        prediction_failures: Optional[list] = None,
        model_error: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize category prediction error.
        
        Args:
            message: Error description
            prediction_failures: List of transactions that failed prediction
            model_error: Specific model error message
            **kwargs: Additional context passed to parent
        """
        context = kwargs.get('context', {})
        if prediction_failures:
            context['prediction_failures'] = prediction_failures
        if model_error:
            context['model_error'] = model_error
        
        super().__init__(message, error_code="CATEGORY_PREDICTION_FAILED", context=context)
        self.prediction_failures = prediction_failures or []
        self.model_error = model_error