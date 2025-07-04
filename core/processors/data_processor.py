"""
Main data processor class for bank statement data transformation.

This module provides the main DataProcessor class that orchestrates the entire
data processing pipeline from raw DataFrames to standardized, validated data
ready for database persistence.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from .schemas import ProcessingConfig, ProcessingResult, ValidationResult, ErrorReport, ProcessingMode
from .exceptions import DataProcessorError, ColumnMappingError, ValidationError
from .column_mapper import ColumnMapper


logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Main data processor for bank statement transformation.
    
    Orchestrates the complete data processing pipeline including column mapping,
    data validation, AI categorization, and data cleaning to convert raw parsed
    bank statement data into standardized pandas DataFrames.
    """
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize the data processor.
        
        Args:
            config: Processing configuration. If None, uses default configuration.
        """
        self.config = config or ProcessingConfig()
        self.column_mapper = ColumnMapper(self.config)
        
        # Initialize other components (will be implemented in later phases)
        from .data_validator import DataValidator
        self._data_validator = DataValidator(self.config)
        self._category_predictor = None  # TODO: Implement in Phase 4
        from .data_cleaner import DataCleaner
        self._data_cleaner = DataCleaner(self.config)
        
        logger.info("DataProcessor initialized with configuration")
    
    def process_dataframe(
        self, 
        df: pd.DataFrame, 
        source_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[pd.DataFrame, ProcessingResult]:
        """
        Process a raw DataFrame through the complete pipeline.
        
        Args:
            df: Raw DataFrame from file parser
            source_info: Optional metadata about the data source
            
        Returns:
            Tuple of (processed_dataframe, processing_result)
            
        Raises:
            DataProcessorError: If processing fails critically
        """
        start_time = time.time()
        logger.info(f"Starting data processing for DataFrame with {len(df)} rows, {len(df.columns)} columns")
        
        try:
            # Initialize processing result
            result = ProcessingResult(
                success=False,
                processed_rows=len(df),
                output_rows=0,
                processing_time_seconds=0.0
            )
            
            # Step 1: Column Mapping
            processed_df, column_mappings = self._execute_column_mapping(df)
            result.column_mappings = column_mappings
            
            # Step 2: Data Validation (placeholder for Phase 3)
            if self.config.mode != ProcessingMode.RECOVERY:
                validation_result = self._execute_validation(processed_df)
                result.validation_result = validation_result
                
                if not validation_result.is_valid and self.config.mode == ProcessingMode.STRICT:
                    raise ValidationError("Data validation failed in strict mode")
            
            # Step 3: AI Categorization (placeholder for Phase 4)
            if self.config.enable_ai_categorization:
                processed_df, ai_stats = self._execute_categorization(processed_df)
                result.ai_predictions = ai_stats.get('predictions_made', 0)
                result.confidence_scores = ai_stats.get('confidence_scores', [])
            
            # Step 4: Data Cleaning (placeholder for Phase 5)
            if self.config.clean_descriptions or self.config.standardize_amounts:
                processed_df = self._execute_cleaning(processed_df)
            
            # Finalize result
            result.success = True
            result.output_rows = len(processed_df)
            result.processing_time_seconds = time.time() - start_time
            result.data_quality_score = self._calculate_quality_score(processed_df, result.validation_result)
            
            logger.info(f"Data processing completed successfully in {result.processing_time_seconds:.2f}s")
            return processed_df, result
            
        except Exception as e:
            # Handle processing errors
            processing_time = time.time() - start_time
            error_report = self._create_error_report(e, source_info)
            
            result = ProcessingResult(
                success=False,
                processed_rows=len(df),
                output_rows=0,
                processing_time_seconds=processing_time,
                error_report=error_report
            )
            
            if self.config.mode == ProcessingMode.STRICT:
                raise DataProcessorError(f"Processing failed: {str(e)}") from e
            
            logger.error(f"Data processing failed: {str(e)}")
            return df, result  # Return original DataFrame on failure
    
    def _execute_column_mapping(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """
        Execute column mapping step of the pipeline.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (mapped_dataframe, column_mappings)
        """
        logger.debug("Executing column mapping step")
        
        try:
            column_mappings, unmapped_columns = self.column_mapper.map_columns(df)
            
            if unmapped_columns:
                logger.warning(f"Unmapped columns: {unmapped_columns}")
            
            # Create new DataFrame with standardized column names
            mapped_df = df.copy()
            mapped_df = mapped_df.rename(columns=column_mappings)
            
            # Add any missing required columns with default values
            standard_schema = self.column_mapper.get_standard_schema()
            for col_type, dtype in standard_schema.items():
                if col_type not in mapped_df.columns:
                    # Find mapping rule for this column type
                    rule = next(
                        (r for r in self.column_mapper._get_all_mapping_rules() 
                         if r.target_column == col_type), 
                        None
                    )
                    if rule and rule.default_value is not None:
                        mapped_df[col_type] = rule.default_value
                        logger.debug(f"Added default column '{col_type}' with value '{rule.default_value}'")
            # Ensure required db_interface columns are present
            required_db_columns = ['description', 'amount', 'transaction_date', 'category', 'sub_category']
            for col in required_db_columns:
                if col not in mapped_df.columns:
                    if col == 'category':
                        mapped_df[col] = 'Uncategorized'
                        logger.debug(f"Added default column '{col}' with value 'Uncategorized'")
                    elif col == 'sub_category':
                        mapped_df[col] = ''
                        logger.debug(f"Added default column '{col}' with empty value")
                    else:
                        # Find mapping rule for this column type
                        rule = next(
                            (r for r in self.column_mapper._get_all_mapping_rules() 
                             if r.target_column == col), 
                            None
                        )
                        if rule and rule.default_value is not None:
                            mapped_df[col] = rule.default_value
                            logger.debug(f"Added default column '{col}' with value '{rule.default_value}'")
            
            return mapped_df, column_mappings
            
        except ColumnMappingError:
            raise  # Re-raise column mapping errors
        except Exception as e:
            raise DataProcessorError(f"Column mapping failed: {str(e)}") from e
    
    def _execute_validation(self, df: pd.DataFrame) -> ValidationResult:
        """
        Execute data validation step (placeholder for Phase 3).
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Validation result
        """
        logger.debug("Executing data validation step (placeholder)")
        
        # TODO: Implement in Phase 3
        # For now, return a basic validation result
        return ValidationResult(
            is_valid=True,
            total_rows=len(df),
            valid_rows=len(df),
            issues=[],
            statistics={"placeholder": True}
        )
    
    def _execute_categorization(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Execute AI categorization step (placeholder for Phase 4).
        
        Args:
            df: DataFrame to categorize
            
        Returns:
            Tuple of (categorized_dataframe, ai_statistics)
        """
        logger.debug("Executing AI categorization step (placeholder)")
        
        # TODO: Implement in Phase 4
        # For now, return unchanged DataFrame
        return df, {
            'predictions_made': 0,
            'confidence_scores': [],
            'placeholder': True
        }
    
    def _execute_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute data cleaning step (placeholder for Phase 5).
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        logger.debug("Executing data cleaning step (placeholder)")
        
        # TODO: Implement in Phase 5
        # For now, return unchanged DataFrame
        return df
    
    def _calculate_quality_score(
        self, 
        df: pd.DataFrame, 
        validation_result: Optional[ValidationResult]
    ) -> float:
        """
        Calculate overall data quality score.
        
        Args:
            df: Processed DataFrame
            validation_result: Validation results
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not validation_result:
            return 0.8  # Default score when validation is skipped
        
        if validation_result.total_rows == 0:
            return 0.0
        
        # Base score from validation success rate
        base_score = validation_result.valid_rows / validation_result.total_rows
        
        # Adjust for error severity
        error_penalty = validation_result.error_count * 0.1
        warning_penalty = validation_result.warning_count * 0.05
        
        quality_score = max(0.0, base_score - error_penalty - warning_penalty)
        return min(1.0, quality_score)
    
    def _create_error_report(
        self, 
        error: Exception, 
        source_info: Optional[Dict[str, Any]]
    ) -> ErrorReport:
        """
        Create detailed error report for processing failures.
        
        Args:
            error: Exception that occurred
            source_info: Optional source information
            
        Returns:
            Detailed error report
        """
        error_type = type(error).__name__
        context = {'source_info': source_info} if source_info else {}
        
        # Add specific context based on error type
        if isinstance(error, ColumnMappingError):
            context.update({
                'unmapped_columns': error.unmapped_columns,
                'missing_required_columns': error.missing_required_columns
            })
        elif isinstance(error, ValidationError):
            context.update({
                'validation_errors': error.validation_errors,
                'failed_rows': error.failed_rows
            })
        
        # Generate suggestions based on error type
        suggestions = self._generate_error_suggestions(error)
        
        return ErrorReport(
            error_type=error_type,
            message=str(error),
            context=context,
            suggestions=suggestions,
            affected_data={'row_count': context.get('source_info', {}).get('row_count')}
        )
    
    def _generate_error_suggestions(self, error: Exception) -> List[str]:
        """
        Generate actionable suggestions for resolving errors.
        
        Args:
            error: Exception that occurred
            
        Returns:
            List of suggested actions
        """
        suggestions = []
        
        if isinstance(error, ColumnMappingError):
            suggestions.extend([
                "Check if the input file has the expected column headers",
                "Verify that required columns (date, description, amount) are present",
                "Consider adding custom mapping rules for non-standard column names",
                "Review the file format and ensure it matches expected bank statement structure"
            ])
        elif isinstance(error, ValidationError):
            suggestions.extend([
                "Check data formats (dates, amounts) in the source file",
                "Verify that all required fields have valid values",
                "Consider using lenient processing mode to handle minor data issues",
                "Review and clean the source data before processing"
            ])
        else:
            suggestions.extend([
                "Check the input file format and structure",
                "Verify that the file is not corrupted",
                "Try processing with recovery mode enabled",
                "Contact support if the issue persists"
            ])
        
        return suggestions
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics and configuration information.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'config': {
                'mode': self.config.mode,
                'ai_enabled': self.config.enable_ai_categorization,
                'validation_enabled': self.config.validate_dates and self.config.validate_amounts,
                'cleaning_enabled': self.config.clean_descriptions or self.config.standardize_amounts
            },
            'mapping_rules': len(self.config.mapping_rules),
            'default_rules': len(self.column_mapper._default_rules),
            'supported_column_types': list(self.column_mapper.get_standard_schema().keys())
        }