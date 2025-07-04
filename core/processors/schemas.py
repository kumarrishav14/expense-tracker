"""
Pydantic schemas for data processor configuration and results.

This module defines all Pydantic models used for configuration, validation,
and result reporting throughout the data processing pipeline.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class ProcessingMode(str, Enum):
    """Processing mode enumeration."""
    STRICT = "strict"  # Fail on any validation error
    LENIENT = "lenient"  # Continue processing with warnings
    RECOVERY = "recovery"  # Attempt error recovery where possible


class ColumnType(str, Enum):
    """Standard column types for mapping."""
    DATE = "transaction_date"
    DESCRIPTION = "description"
    AMOUNT = "amount"
    BALANCE = "balance"
    REFERENCE = "reference"
    CATEGORY = "category"
    SUB_CATEGORY = "sub_category"
    ACCOUNT = "account"


class ValidationSeverity(str, Enum):
    """Validation error severity levels."""
    ERROR = "error"  # Critical error, processing should stop
    WARNING = "warning"  # Non-critical issue, processing can continue
    INFO = "info"  # Informational message


class ColumnMappingRule(BaseModel):
    """
    Configuration for column mapping rules.
    
    Defines how raw DataFrame columns should be mapped to standard schema columns
    using pattern matching, similarity scoring, and manual overrides.
    """
    
    target_column: ColumnType = Field(..., description="Target standard column type")
    patterns: List[str] = Field(default_factory=list, description="Regex patterns to match column names")
    keywords: List[str] = Field(default_factory=list, description="Keywords for fuzzy matching")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    required: bool = Field(default=True, description="Whether this column is required")
    default_value: Optional[Any] = Field(default=None, description="Default value if column is missing")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ProcessingConfig(BaseModel):
    """
    Configuration for data processing pipeline.
    
    Defines all configurable parameters for the data processing pipeline
    including validation rules, mapping settings, and processing behavior.
    """
    
    # Processing behavior
    mode: ProcessingMode = Field(default=ProcessingMode.LENIENT, description="Processing mode")
    max_errors: int = Field(default=100, ge=0, description="Maximum errors before stopping")
    enable_ai_categorization: bool = Field(default=True, description="Enable AI-powered categorization")
    
    # Column mapping configuration
    mapping_rules: List[ColumnMappingRule] = Field(default_factory=list, description="Column mapping rules")
    auto_detect_columns: bool = Field(default=True, description="Enable automatic column detection")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Global similarity threshold")
    
    # Validation configuration
    validate_dates: bool = Field(default=True, description="Enable date validation")
    validate_amounts: bool = Field(default=True, description="Enable amount validation")
    validate_duplicates: bool = Field(default=True, description="Enable duplicate detection")
    date_formats: List[str] = Field(default_factory=lambda: ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"], description="Accepted date formats")
    
    # Data cleaning configuration
    clean_descriptions: bool = Field(default=True, description="Enable description cleaning")
    standardize_amounts: bool = Field(default=True, description="Enable amount standardization")
    handle_missing_data: bool = Field(default=True, description="Enable missing data handling")
    
    # AI categorization configuration
    ai_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum AI confidence score")
    fallback_to_rules: bool = Field(default=True, description="Fallback to rule-based categorization")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ValidationIssue(BaseModel):
    """
    Individual validation issue details.
    
    Represents a single validation problem found during data processing
    with detailed information for debugging and user feedback.
    """
    
    severity: ValidationSeverity = Field(..., description="Issue severity level")
    message: str = Field(..., description="Human-readable issue description")
    column: Optional[str] = Field(default=None, description="Column where issue was found")
    row_index: Optional[int] = Field(default=None, description="Row index where issue was found")
    value: Optional[Any] = Field(default=None, description="Problematic value")
    suggestion: Optional[str] = Field(default=None, description="Suggested fix or action")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class ValidationResult(BaseModel):
    """
    Result of data validation process.
    
    Contains comprehensive information about validation outcomes including
    issues found, statistics, and recommendations for data quality improvement.
    """
    
    is_valid: bool = Field(..., description="Whether validation passed overall")
    total_rows: int = Field(..., ge=0, description="Total number of rows validated")
    valid_rows: int = Field(..., ge=0, description="Number of rows that passed validation")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of validation issues")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="Validation statistics")
    
    @validator('valid_rows')
    def validate_row_counts(cls, v, values):
        """Ensure valid_rows doesn't exceed total_rows."""
        if 'total_rows' in values and v > values['total_rows']:
            raise ValueError("valid_rows cannot exceed total_rows")
        return v
    
    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return len([issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR])
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return len([issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING])


class ErrorReport(BaseModel):
    """
    Comprehensive error report for processing failures.
    
    Provides detailed information about processing errors with actionable
    suggestions for resolution and debugging information.
    """
    
    error_type: str = Field(..., description="Type of error that occurred")
    message: str = Field(..., description="Primary error message")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional error context")
    suggestions: List[str] = Field(default_factory=list, description="Suggested actions to resolve the error")
    affected_data: Optional[Dict[str, Any]] = Field(default=None, description="Information about affected data")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ProcessingResult(BaseModel):
    """
    Complete result of data processing pipeline.
    
    Contains all information about the processing outcome including success status,
    validation results, performance metrics, and any errors encountered.
    """
    
    success: bool = Field(..., description="Whether processing completed successfully")
    processed_rows: int = Field(..., ge=0, description="Number of rows processed")
    output_rows: int = Field(..., ge=0, description="Number of rows in output DataFrame")
    validation_result: Optional[ValidationResult] = Field(default=None, description="Validation results")
    error_report: Optional[ErrorReport] = Field(default=None, description="Error details if processing failed")
    
    # Processing statistics
    processing_time_seconds: float = Field(..., ge=0.0, description="Total processing time")
    column_mappings: Dict[str, str] = Field(default_factory=dict, description="Applied column mappings")
    categories_assigned: int = Field(default=0, ge=0, description="Number of categories assigned")
    ai_predictions: int = Field(default=0, ge=0, description="Number of AI predictions made")
    
    # Quality metrics
    data_quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall data quality score")
    confidence_scores: List[float] = Field(default_factory=list, description="AI confidence scores")
    
    @validator('output_rows')
    def validate_output_rows(cls, v, values):
        """Ensure output_rows doesn't exceed processed_rows in normal cases."""
        if 'processed_rows' in values and v > values['processed_rows']:
            # This could be valid in some cases (data expansion), so just warn
            pass
        return v
    
    @property
    def success_rate(self) -> float:
        """Calculate processing success rate."""
        if self.processed_rows == 0:
            return 0.0
        return self.output_rows / self.processed_rows
    
    @property
    def average_confidence(self) -> float:
        """Calculate average AI confidence score."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)