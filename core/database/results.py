"""
Structured result classes for database operations.

This module provides standardized result structures for database operations,
enabling structured error reporting and consistent API responses across
the database interface.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class OperationResult:
    """
    Structured result for single database operations.

    Provides comprehensive information about the operation outcome,
    including success status, error details, and metadata.

    Attributes:
        success (bool): Whether the operation completed successfully.
        error_message (Optional[str]): Human-readable error description.
        error_type (Optional[str]): Type of exception that occurred.
        error_category (Optional[str]): Category of error for classification.
        affected_rows (int): Number of database rows affected.
        data (Optional[Dict[str, Any]]): Additional operation metadata.
        is_retryable (bool): Whether the operation can be retried safely.

    Usage:
        # Success case
        result = OperationResult(success=True, affected_rows=1)

        # Error case
        result = OperationResult(
            success=False,
            error_message="Constraint violation",
            error_type="IntegrityError",
            error_category="constraint_violation",
            is_retryable=False
        )
    """
    success: bool
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error_category: Optional[str] = None
    affected_rows: int = 0
    data: Optional[Dict[str, Any]] = None
    is_retryable: bool = False


@dataclass
class BatchOperationResult:
    """
    Structured result for batch database operations.

    Provides detailed information about batch operation outcomes,
    including partial success scenarios and individual item tracking.

    Attributes:
        success (bool): Whether all items in the batch succeeded.
        successful_count (int): Number of items processed successfully.
        failed_count (int): Number of items that failed processing.
        total_processed (int): Total number of items in the batch.
        errors (List[Dict[str, Any]]): Details of individual item failures.
        successful_items (List[Any]): Items that were processed successfully.
        failed_items (List[Any]): Items that failed processing.
        error_message (Optional[str]): Overall batch operation error message.
        is_retryable (bool): Whether the entire batch can be retried safely.

    Usage:
        # Complete success
        result = BatchOperationResult(
            success=True,
            successful_count=10,
            total_processed=10
        )

        # Partial success
        result = BatchOperationResult(
            success=False,
            successful_count=8,
            failed_count=2,
            total_processed=10,
            errors=[
                {"item": item1, "error": "Constraint violation"},
                {"item": item2, "error": "Data validation failed"}
            ]
        )
    """
    success: bool
    successful_count: int = 0
    failed_count: int = 0
    total_processed: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    successful_items: List[Any] = field(default_factory=list)
    failed_items: List[Any] = field(default_factory=list)
    error_message: Optional[str] = None
    is_retryable: bool = False

    def add_success(self, item: Any) -> None:
        """
        Add a successfully processed item to the result.

        Args:
            item (Any): The item that was processed successfully.
        """
        self.successful_items.append(item)
        self.successful_count += 1
        self.total_processed += 1

    def add_failure(self, item: Any, error: str) -> None:
        """
        Add a failed item to the result.

        Args:
            item (Any): The item that failed processing.
            error (str): The error message for this item.
        """
        self.failed_items.append(item)
        self.errors.append({"item": item, "error": error})
        self.failed_count += 1
        self.total_processed += 1
        self.success = False

    @property
    def success_rate(self) -> float:
        """
        Calculate the success rate as a percentage.

        Returns:
            float: Success rate between 0.0 and 1.0.
        """
        if self.total_processed == 0:
            return 1.0
        return self.successful_count / self.total_processed
