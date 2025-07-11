"""
Shared fixtures and test data for DataProcessor tests.

Provides reusable test data and fixtures following the test plan architecture.
"""

import pandas as pd
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture
def data_processor():
    """Create a DataProcessor instance for testing."""
    from core.processors.data_processor import DataProcessor
    return DataProcessor()


@pytest.fixture
def standard_raw_data() -> pd.DataFrame:
    """Standard bank statement format with exact column name matches."""
    return pd.DataFrame({
        'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'description': ['Amazon Purchase', 'Salary Credit', 'ATM Withdrawal'],
        'amount': [1500.50, 50000.00, 2000.00],
        'category': [None, None, None],
        'sub_category': [None, None, None]
    })


@pytest.fixture
def variant_column_names_data() -> pd.DataFrame:
    """Bank statement with variant column naming conventions."""
    return pd.DataFrame({
        'date': ['15/01/2024', '16/01/2024', '17/01/2024'],
        'transaction details': ['Swiggy Food Order', 'Metro Card Recharge', 'Movie Ticket'],
        'transaction amount': ['Rs 450.75', '₹ 500.00', '350'],
        'type': [None, None, None]
    })


@pytest.fixture
def debit_credit_format_data() -> pd.DataFrame:
    """Bank statement with separate debit and credit columns."""
    return pd.DataFrame({
        'posting_date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'particulars': ['Restaurant Bill', 'Salary', 'Cash Withdrawal'],
        'debit': [750.00, None, 1000.00],
        'credit': [None, 45000.00, None]
    })


@pytest.fixture
def messy_data() -> pd.DataFrame:
    """Mixed valid/invalid data with formatting issues."""
    return pd.DataFrame({
        'date': ['15-01-2024', 'invalid_date', '17/01/2024', ''],
        'description': ['Valid Transaction', '', 'Another Valid', '   '],
        'amount': ['1,500.50', 'not_a_number', '2000', '0'],
        'extra_column': ['ignore', 'this', 'column', 'data']
    })


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Empty DataFrame for error testing."""
    return pd.DataFrame()


@pytest.fixture
def no_mappable_columns_data() -> pd.DataFrame:
    """DataFrame with no mappable columns."""
    return pd.DataFrame({
        'random_col1': ['data1', 'data2'],
        'random_col2': ['data3', 'data4'],
        'unmappable': ['data5', 'data6']
    })


@pytest.fixture
def expected_standard_output() -> pd.DataFrame:
    """Expected output for standard raw data after processing."""
    # TODO: Enable when AI backend is available - Update expected categories
    return pd.DataFrame({
        'description': ['Amazon Purchase', 'Salary Credit', 'ATM Withdrawal'],
        'amount': [1500.50, 50000.00, 2000.00],
        'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16', '2024-01-17']),
        'category': [None, None, None],  # Will be populated by AI when available
        'sub_category': [None, None, None]  # Will be populated by AI when available
    })


@pytest.fixture
def categorization_test_data() -> pd.DataFrame:
    """Data specifically for testing AI categorization logic."""
    return pd.DataFrame({
        'transaction_date': pd.to_datetime(['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19']),
        'description': [
            'Amazon Shopping Purchase',
            'Swiggy Food Delivery',
            'Unknown Merchant',
            'UPI Transfer to John',
            'ATM Cash Withdrawal'
        ],
        'amount': [2500.00, 450.75, 150.00, 15000.00, 2000.00],
        'category': [None, None, None, None, None],
        'sub_category': [None, None, None, None, None]
    })


@pytest.fixture
def large_dataset() -> pd.DataFrame:
    """Larger dataset for integration testing."""
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(50)]
    descriptions = [
        'Amazon Purchase', 'Swiggy Order', 'Salary Credit', 'ATM Withdrawal', 'Metro Recharge',
        'Restaurant Bill', 'Uber Ride', 'Netflix Subscription', 'Electricity Bill', 'Medical Store'
    ] * 5
    amounts = [1500.50, 450.75, 50000.00, 2000.00, 500.00] * 10
    
    return pd.DataFrame({
        'transaction_date': dates,
        'description': descriptions,
        'amount': amounts
    })


@pytest.fixture
def currency_symbols_data() -> pd.DataFrame:
    """Data with various currency symbols and formatting."""
    return pd.DataFrame({
        'date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'details': ['Purchase 1', 'Purchase 2', 'Purchase 3'],
        'amount': ['Rs 1,500.50', '₹ 2,000.00', '$150.75']
    })


@pytest.fixture
def duplicate_transactions_data() -> pd.DataFrame:
    """Data with duplicate transactions for testing deduplication."""
    return pd.DataFrame({
        'transaction_date': ['2024-01-15', '2024-01-15', '2024-01-16'],
        'description': ['Amazon Purchase', 'Amazon Purchase', 'Different Purchase'],
        'amount': [1500.50, 1500.50, 2000.00]
    })


@pytest.fixture
def edge_case_amounts() -> pd.DataFrame:
    """Data with edge case amounts (very small, very large, zero)."""
    return pd.DataFrame({
        'transaction_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18'],
        'description': ['Small Purchase', 'Large Purchase', 'Zero Amount', 'Regular Purchase'],
        'amount': [0.01, 100000.00, 0.00, 1500.50]
    })


def create_test_dataframe(columns: Dict[str, Any]) -> pd.DataFrame:
    """Helper function to create test DataFrames with specified columns."""
    return pd.DataFrame(columns)


def assert_dataframe_schema(df: pd.DataFrame, expected_columns: list) -> None:
    """Helper function to assert DataFrame has expected schema."""
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check data types
    assert df['amount'].dtype in ['float64', 'int64'], "Amount should be numeric"
    assert pd.api.types.is_datetime64_any_dtype(df['transaction_date']), "transaction_date should be datetime"
    assert df['description'].dtype == 'object', "description should be string/object type"
    assert df['category'].dtype == 'object', "category should be string/object type"
    assert df['sub_category'].dtype == 'object', "sub_category should be string/object type"


def assert_processing_summary(summary: Dict, original_rows: int, expected_processed: int) -> None:
    """Helper function to assert processing summary is correct."""
    assert 'original_rows' in summary
    assert 'processed_rows' in summary
    assert 'rows_removed' in summary
    assert 'categories_assigned' in summary
    assert 'processing_success' in summary
    
    assert summary['original_rows'] == original_rows
    assert summary['processed_rows'] == expected_processed
    assert summary['rows_removed'] == original_rows - expected_processed
    assert summary['processing_success'] is True


@pytest.fixture
def mock_ai_categorization(mocker):
    """
    Mocks the AI categorization call to return predictable categories.
    """
    def mock_categorize(description: str, categories: list) -> str:
        description = description.lower()
        if "medical" in description or "store" in description:
            return "Healthcare"
        if "swiggy" in description or "restaurant" in description or "zomato" in description:
            return "Food & Dining"
        if "amazon" in description or "flipkart" in description:
            return "Shopping"
        if "salary" in description:
            return "Salary"
        if "atm" in description:
            return "ATM"
        if "bill" in description:
            return "Bills & Utilities"
        if "uber" in description or "metro" in description:
            return "Transportation"
        if "netflix" in description:
            return "Entertainment"
        if "transfer" in description:
            return "Transfer"
        return "Other"

    mocker.patch(
        'core.processors.data_processor.categorize_expense',
        side_effect=mock_categorize,
        create=True
    )
