"""
Data validation engine for the data processor.

This module provides comprehensive data validation capabilities including
business rule validation, data type checking, consistency validation,
and quality assessment for bank statement data.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import pandas as pd
from dateutil import parser as date_parser

from .schemas import (
    ValidationResult, 
    ValidationIssue, 
    ValidationSeverity, 
    ProcessingConfig,
    ColumnType
)
from .exceptions import ValidationError


logger = logging.getLogger(__name__)


class DataValidator:
    """
    Comprehensive data validation engine.
    
    Validates bank statement data for business rules, data types, consistency,
    and quality to ensure data integrity before database persistence.
    """
    
    def __init__(self, config: ProcessingConfig):
        """
        Initialize the data validator.
        
        Args:
            config: Processing configuration with validation settings
        """
        self.config = config
        self._date_formats = config.date_formats
        self._validation_rules = self._create_validation_rules()
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate a complete DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Comprehensive validation result
            
        Raises:
            ValidationError: If critical validation failures occur
        """
        logger.info(f"Starting validation for DataFrame with {len(df)} rows")
        
        issues = []
        statistics = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'validation_start_time': datetime.now().isoformat()
        }
        
        try:
            # Step 1: Validate required columns
            if self.config.validate_dates or self.config.validate_amounts:
                column_issues = self._validate_required_columns(df)
                issues.extend(column_issues)
            
            # Step 2: Validate data types
            type_issues = self._validate_data_types(df)
            issues.extend(type_issues)
            
            # Step 3: Validate business rules
            business_issues = self._validate_business_rules(df)
            issues.extend(business_issues)
            
            # Step 4: Validate data consistency
            consistency_issues = self._validate_data_consistency(df)
            issues.extend(consistency_issues)
            
            # Step 5: Check for duplicates
            if self.config.validate_duplicates:
                duplicate_issues = self._validate_duplicates(df)
                issues.extend(duplicate_issues)
            
            # Calculate validation statistics
            error_count = len([i for i in issues if i.severity == ValidationSeverity.ERROR])
            warning_count = len([i for i in issues if i.severity == ValidationSeverity.WARNING])
            valid_rows = len(df) - len(set(i.row_index for i in issues if i.row_index is not None and i.severity == ValidationSeverity.ERROR))
            
            statistics.update({
                'error_count': error_count,
                'warning_count': warning_count,
                'valid_rows': valid_rows,
                'validation_end_time': datetime.now().isoformat()
            })
            
            is_valid = error_count == 0
            
            logger.info(f"Validation completed: {valid_rows}/{len(df)} rows valid, {error_count} errors, {warning_count} warnings")
            
            return ValidationResult(
                is_valid=is_valid,
                total_rows=len(df),
                valid_rows=valid_rows,
                issues=issues,
                statistics=statistics
            )
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {str(e)}")
            raise ValidationError(f"Validation process failed: {str(e)}") from e
    
    def _validate_required_columns(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Validate that required columns are present and not empty.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        required_columns = ["transaction_date", "description", "amount"]
        
        for col in required_columns:
            if col not in df.columns:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Required column '{col}' is missing",
                    column=col,
                    error_code="MISSING_REQUIRED_COLUMN",
                    suggestion=f"Ensure the input data contains a '{col}' column"
                ))
            elif df[col].isna().all():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Required column '{col}' is completely empty",
                    column=col,
                    error_code="EMPTY_REQUIRED_COLUMN",
                    suggestion=f"Ensure the '{col}' column contains valid data"
                ))
        
        return issues
    
    def _validate_data_types(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Validate data types and formats.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Validate date column
        if "transaction_date" in df.columns and self.config.validate_dates:
            date_issues = self._validate_date_column(df, "transaction_date")
            issues.extend(date_issues)
        
        # Validate amount column
        if "amount" in df.columns and self.config.validate_amounts:
            amount_issues = self._validate_amount_column(df, "amount")
            issues.extend(amount_issues)
        
        # Validate balance column if present
        if "balance" in df.columns:
            balance_issues = self._validate_amount_column(df, "balance")
            issues.extend(balance_issues)
        
        return issues
    
    def _validate_date_column(self, df: pd.DataFrame, column: str) -> List[ValidationIssue]:
        """
        Validate date column format and values.
        
        Args:
            df: DataFrame to validate
            column: Date column name
            
        Returns:
            List of validation issues
        """
        issues = []
        
        for idx, value in df[column].items():
            if pd.isna(value):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing date value",
                    column=column,
                    row_index=idx,
                    value=value,
                    error_code="MISSING_DATE",
                    suggestion="Provide a valid date value"
                ))
                continue
            
            # Try to parse the date
            parsed_date = self._parse_date(value)
            if parsed_date is None:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid date format: '{value}'",
                    column=column,
                    row_index=idx,
                    value=value,
                    error_code="INVALID_DATE_FORMAT",
                    suggestion=f"Use one of these formats: {', '.join(self._date_formats)}"
                ))
                continue
            
            # Check if date is reasonable (not too far in future/past)
            current_date = datetime.now().date()
            if isinstance(parsed_date, datetime):
                parsed_date = parsed_date.date()
            
            if parsed_date > current_date:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Future date detected: '{value}'",
                    column=column,
                    row_index=idx,
                    value=value,
                    error_code="FUTURE_DATE",
                    suggestion="Verify that future dates are correct"
                ))
            elif (current_date - parsed_date).days > 3650:  # More than 10 years ago
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Very old date detected: '{value}'",
                    column=column,
                    row_index=idx,
                    value=value,
                    error_code="OLD_DATE",
                    suggestion="Verify that old dates are correct"
                ))
        
        return issues
    
    def _validate_amount_column(self, df: pd.DataFrame, column: str) -> List[ValidationIssue]:
        """
        Validate amount/balance column format and values.
        
        Args:
            df: DataFrame to validate
            column: Amount column name
            
        Returns:
            List of validation issues
        """
        issues = []
        
        for idx, value in df[column].items():
            if pd.isna(value):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing {column} value",
                    column=column,
                    row_index=idx,
                    value=value,
                    error_code="MISSING_AMOUNT",
                    suggestion=f"Provide a valid {column} value"
                ))
                continue
            
            # Try to convert to float
            try:
                numeric_value = float(value)
                
                # Check for reasonable amount ranges
                if abs(numeric_value) > 1000000:  # More than 1 million
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Very large {column}: {numeric_value}",
                        column=column,
                        row_index=idx,
                        value=value,
                        error_code="LARGE_AMOUNT",
                        suggestion=f"Verify that large {column} values are correct"
                    ))
                
                # For transaction amounts, zero values might be suspicious
                if column == "amount" and numeric_value == 0:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Zero transaction amount",
                        column=column,
                        row_index=idx,
                        value=value,
                        error_code="ZERO_AMOUNT",
                        suggestion="Verify that zero amounts are correct"
                    ))
                
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid {column} format: '{value}'",
                    column=column,
                    row_index=idx,
                    value=value,
                    error_code="INVALID_AMOUNT_FORMAT",
                    suggestion=f"Ensure {column} values are numeric"
                ))
        
        return issues
    
    def _validate_business_rules(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Validate business logic rules.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for required field combinations
        if "transaction_date" in df.columns and "amount" in df.columns:
            for idx, row in df.iterrows():
                # Both date and amount should be present for valid transactions
                if pd.isna(row["transaction_date"]) and not pd.isna(row["amount"]):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Transaction has amount but no date",
                        row_index=idx,
                        error_code="MISSING_DATE_FOR_TRANSACTION",
                        suggestion="Ensure all transactions have both date and amount"
                    ))
                elif not pd.isna(row["transaction_date"]) and pd.isna(row["amount"]):
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message="Transaction has date but no amount",
                        row_index=idx,
                        error_code="MISSING_AMOUNT_FOR_TRANSACTION",
                        suggestion="Ensure all transactions have both date and amount"
                    ))
        
        return issues
    
    def _validate_data_consistency(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Validate data consistency and relationships.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check date ordering
        if "transaction_date" in df.columns:
            date_issues = self._validate_date_ordering(df)
            issues.extend(date_issues)
        
        # Check balance consistency if balance column exists
        if "balance" in df.columns and "amount" in df.columns:
            balance_issues = self._validate_balance_consistency(df)
            issues.extend(balance_issues)
        
        return issues
    
    def _validate_date_ordering(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Validate that dates are in reasonable order.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Parse all dates first
        parsed_dates = []
        for idx, value in df["transaction_date"].items():
            parsed_date = self._parse_date(value)
            parsed_dates.append((idx, parsed_date))
        
        # Check for significant date jumps (more than 1 year backwards)
        valid_dates = [(idx, dt) for idx, dt in parsed_dates if dt is not None]
        for i in range(1, len(valid_dates)):
            prev_idx, prev_date = valid_dates[i-1]
            curr_idx, curr_date = valid_dates[i]
            
            if isinstance(prev_date, datetime):
                prev_date = prev_date.date()
            if isinstance(curr_date, datetime):
                curr_date = curr_date.date()
            
            if prev_date > curr_date and (prev_date - curr_date).days > 365:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message=f"Significant date jump backwards from {prev_date} to {curr_date}",
                    column="transaction_date",
                    row_index=curr_idx,
                    error_code="DATE_JUMP_BACKWARDS",
                    suggestion="Verify date ordering in the source data"
                ))
        
        return issues
    
    def _validate_balance_consistency(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Validate balance consistency with transaction amounts.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # This is a simplified check - in reality, balance calculation
        # depends on the specific bank's format and conventions
        for i in range(1, len(df)):
            try:
                prev_balance = float(df.iloc[i-1]["balance"])
                curr_balance = float(df.iloc[i]["balance"])
                curr_amount = float(df.iloc[i]["amount"])
                
                expected_balance = prev_balance + curr_amount
                difference = abs(curr_balance - expected_balance)
                
                # Allow for small rounding differences
                if difference > 0.01:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Balance inconsistency: expected {expected_balance}, got {curr_balance}",
                        column="balance",
                        row_index=i,
                        error_code="BALANCE_INCONSISTENCY",
                        suggestion="Verify balance calculations or check for missing transactions"
                    ))
            except (ValueError, TypeError, KeyError):
                # Skip if we can't parse the values
                continue
        
        return issues
    
    def _validate_duplicates(self, df: pd.DataFrame) -> List[ValidationIssue]:
        """
        Check for duplicate transactions.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        # Define columns to check for duplicates
        check_columns = []
        if "transaction_date" in df.columns:
            check_columns.append("transaction_date")
        if "amount" in df.columns:
            check_columns.append("amount")
        if "description" in df.columns:
            check_columns.append("description")
        
        if len(check_columns) >= 2:
            # Find duplicates based on available columns
            duplicates = df.duplicated(subset=check_columns, keep=False)
            duplicate_indices = df[duplicates].index.tolist()
            
            if duplicate_indices:
                for idx in duplicate_indices:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Potential duplicate transaction",
                        row_index=idx,
                        error_code="DUPLICATE_TRANSACTION",
                        suggestion="Review and remove duplicate transactions if necessary"
                    ))
        
        return issues
    
    def _parse_date(self, value: Any) -> Optional[datetime]:
        """
        Parse a date value using configured formats.
        
        Args:
            value: Date value to parse
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        if pd.isna(value):
            return None
        
        # Convert to string if not already
        date_str = str(value).strip()
        
        # Try configured formats first
        for fmt in self._date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try dateutil parser as fallback
        try:
            return date_parser.parse(date_str)
        except (ValueError, TypeError):
            return None
    
    def _create_validation_rules(self) -> Dict[str, Any]:
        """
        Create validation rules based on configuration.
        
        Returns:
            Dictionary of validation rules
        """
        return {
            'validate_dates': self.config.validate_dates,
            'validate_amounts': self.config.validate_amounts,
            'validate_duplicates': self.config.validate_duplicates,
            'date_formats': self.config.date_formats,
            'max_errors': self.config.max_errors
        }