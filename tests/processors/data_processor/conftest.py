"""
Pytest configuration and fixtures for DataProcessor tests.

This module provides shared fixtures and test data for testing
the DataProcessor component with realistic banking scenarios.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import tempfile
import os

from core.processors.data_processor import DataProcessor


@pytest.fixture
def data_processor():
    """Create a DataProcessor instance for testing."""
    return DataProcessor()


@pytest.fixture
def sample_chase_data() -> pd.DataFrame:
    """Sample Chase bank CSV format data."""
    return pd.DataFrame({
        'Transaction Date': ['01/15/2024', '01/16/2024', '01/17/2024'],
        'Description': ['GROCERY STORE PURCHASE', 'GAS STATION', 'RESTAURANT MEAL'],
        'Amount': ['-85.32', '-45.67', '-28.50'],
        'Balance': ['1234.56', '1188.89', '1160.39']
    })


@pytest.fixture
def sample_bofa_data() -> pd.DataFrame:
    """Sample Bank of America CSV format data."""
    return pd.DataFrame({
        'Date': ['1/15/2024', '1/16/2024', '1/17/2024'],
        'Description': ['WHOLE FOODS MARKET', 'SHELL GAS STATION', 'STARBUCKS COFFEE'],
        'Amount': [-85.32, -45.67, -28.50],
        'Running Bal.': [1234.56, 1188.89, 1160.39]
    })


@pytest.fixture
def sample_wells_fargo_data() -> pd.DataFrame:
    """Sample Wells Fargo CSV format data."""
    return pd.DataFrame({
        'Date': ['01/15/2024', '01/16/2024', '01/17/2024'],
        'Amount': ['(85.32)', '(45.67)', '(28.50)'],
        'Description': ['SAFEWAY GROCERY', 'CHEVRON GAS', 'CHIPOTLE RESTAURANT'],
        'Balance': ['1,234.56', '1,188.89', '1,160.39']
    })


@pytest.fixture
def sample_credit_card_data() -> pd.DataFrame:
    """Sample credit card statement format data."""
    return pd.DataFrame({
        'Trans. Date': ['01/15/2024', '01/16/2024', '01/17/2024'],
        'Description': ['AMAZON.COM PURCHASE', 'UBER RIDE', 'NETFLIX SUBSCRIPTION'],
        'Amount': ['$85.32', '$15.50', '$12.99'],
        'Category': ['Shopping', 'Transportation', 'Entertainment']
    })


@pytest.fixture
def sample_manual_entry_data() -> pd.DataFrame:
    """Sample manually entered transaction data."""
    return pd.DataFrame({
        'date': ['2024-01-15', '2024-01-16', '2024-01-17'],
        'description': ['Cash grocery shopping', 'Coffee shop tip', 'Parking meter'],
        'amount': [25.00, 3.50, 2.00],
        'category': ['Groceries', 'Food & Dining', 'Transportation']
    })


@pytest.fixture
def empty_dataframe() -> pd.DataFrame:
    """Empty DataFrame for testing edge cases."""
    return pd.DataFrame()


@pytest.fixture
def malformed_data() -> pd.DataFrame:
    """Malformed data for error testing."""
    return pd.DataFrame({
        'Random Column': ['invalid', 'data', 'here'],
        'Another Column': [1, 2, 3],
        'No Standard Columns': ['test', 'test', 'test']
    })


@pytest.fixture
def large_dataset() -> pd.DataFrame:
    """Large dataset for volume testing (500 transactions)."""
    dates = []
    descriptions = []
    amounts = []
    balances = []
    
    base_date = datetime(2024, 1, 1)
    base_balance = 5000.00
    
    transaction_types = [
        ('GROCERY STORE', -75.50),
        ('GAS STATION', -45.00),
        ('RESTAURANT', -35.25),
        ('COFFEE SHOP', -5.50),
        ('ONLINE PURCHASE', -125.75),
        ('SALARY DEPOSIT', 2500.00),
        ('UTILITY BILL', -85.30),
        ('PHONE BILL', -65.00),
        ('SUBSCRIPTION', -12.99),
        ('ATM WITHDRAWAL', -100.00)
    ]
    
    current_balance = base_balance
    for i in range(500):
        # Generate date
        current_date = base_date + timedelta(days=i // 3)
        dates.append(current_date.strftime('%m/%d/%Y'))
        
        # Pick random transaction type
        desc, amount = transaction_types[i % len(transaction_types)]
        descriptions.append(f"{desc} {i+1}")
        amounts.append(amount)
        
        # Update balance
        current_balance += amount
        balances.append(current_balance)
    
    return pd.DataFrame({
        'Transaction Date': dates,
        'Description': descriptions,
        'Amount': amounts,
        'Balance': balances
    })


@pytest.fixture
def edge_case_data() -> pd.DataFrame:
    """Edge case data with problematic values."""
    return pd.DataFrame({
        'Date': ['01/15/2024', '02/30/2024', 'invalid_date', '01/17/2024'],
        'Description': [
            'Normal transaction',
            'Very long description that goes on and on and contains special characters !@#$%^&*()_+-=[]{}|;:,.<>?',
            '',  # Empty description
            'Unicode transaction: café, naïve, résumé'
        ],
        'Amount': ['100.50', 'invalid_amount', '0', '999999.99'],
        'Balance': ['1000.00', '900.00', '900.00', '1000899.99']
    })


@pytest.fixture
def mixed_format_data() -> List[pd.DataFrame]:
    """Multiple DataFrames with different formats for mixed processing."""
    return [
        pd.DataFrame({  # Chase format
            'Transaction Date': ['01/15/2024', '01/16/2024'],
            'Description': ['GROCERY STORE', 'GAS STATION'],
            'Amount': ['-85.32', '-45.67'],
            'Balance': ['1234.56', '1188.89']
        }),
        pd.DataFrame({  # Manual entry format
            'date': ['2024-01-17', '2024-01-18'],
            'description': ['Cash purchase', 'Tip'],
            'amount': [25.00, 5.00],
            'balance': [1213.89, 1218.89]
        })
    ]


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for file-based testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_file.write('Date,Description,Amount,Balance\n')
    temp_file.write('01/15/2024,GROCERY STORE,-85.32,1234.56\n')
    temp_file.write('01/16/2024,GAS STATION,-45.67,1188.89\n')
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def expected_standard_columns() -> List[str]:
    """Expected standard column names after processing."""
    return ['description', 'amount', 'transaction_date', 'category', 'sub_category']


@pytest.fixture
def mock_ai_categories() -> Dict[str, str]:
    """Mock AI categorization results."""
    return {
        'GROCERY STORE': 'Groceries',
        'GAS STATION': 'Transportation',
        'RESTAURANT': 'Food & Dining',
        'COFFEE SHOP': 'Food & Dining',
        'AMAZON': 'Shopping',
        'NETFLIX': 'Entertainment',
        'SALARY': 'Income',
        'UTILITY': 'Bills & Utilities'
    }