"""
Configurations and fixtures for AI Data Processor tests.
"""
import pytest
import pandas as pd
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

@pytest.fixture
def mock_db_interface(mocker):
    """Mocks the DatabaseInterface to return a fixed category table."""
    mock_categories = pd.DataFrame({
        'name': ['Food & Dining', 'Groceries', 'Restaurants', 'Shopping', 'Electronics', 'Clothing'],
        'parent_category': [None, 'Food & Dining', 'Food & Dining', None, 'Shopping', 'Shopping']
    })
    mocker.patch('core.database.db_interface.DatabaseInterface.get_categories_table', return_value=mock_categories)

@pytest.fixture
def mock_ollama_client(mocker):
    """Mocks the Ollama client to return a predictable JSON response."""
    mock_data = [
        {
            "transaction_date": "2024-07-10",
            "description": "Sample Transaction 1",
            "amount": -100.0,
            "category": "Shopping",
            "sub_category": "Electronics"
        },
        {
            "transaction_date": "2024-07-11",
            "description": "Sample Transaction 2",
            "amount": 5000.0,
            "category": "Salary",
            "sub_category": ""
        }
    ]
    mock_response = json.dumps(mock_data)
    mocker.patch('ai.ollama.factory.get_ollama_client').return_value.generate_completion.return_value = mock_response

@pytest.fixture(params=[
    # Indian Banks
    (pd.DataFrame({
        'Date': ['01/07/2024'], 'Narration': ['UPI/PAYTM/TRANSFER'], 'Debit': [500.00], 'Credit': [None], 'Balance': [10000.00]
    }), -1, 500.00),
    (pd.DataFrame({
        'Transaction Date': ['02-07-2024'], 'Description': ['SALARY CREDIT JULY'], 'Withdrawal Amt.': [None], 'Deposit Amt.': [50000.00], 'Closing Balance': [60000.00]
    }), 1, 50000.00),
    # US Banks
    (pd.DataFrame({
        'Date': ['07/15/2024'], 'Description': ['STARBUCKS'], 'Amount': [-5.75]
    }), -1, 5.75),
    (pd.DataFrame({
        'Transaction Date': ['2024-07-13'], 'Details': ['PAYCHECK DEPOSIT'], 'Debit': [None], 'Credit': [1500.00]
    }), 1, 1500.00),
    # UK Banks
    (pd.DataFrame({
        'Date': ['01/08/2024'], 'Description': ['Supermarket'], 'Amount': [-55.20]
    }), -1, 55.20),
    (pd.DataFrame({
        'Transaction Date': ['02/08/2024'], 'Details': ['Salary'], 'Money In': [2500.00], 'Money Out': [None], 'Balance': [3000.00]
    }), 1, 2500.00),
    # Other variations
    (pd.DataFrame({
        'Date': ['10 Jul 2024'], 'Memo': ['Coffee Shop'], 'Amount': [-4.50]
    }), -1, 4.50),
    (pd.DataFrame({
        'Posting Date': ['2024-07-11'], 'Description': ['ONLINE PAYMENT'], 'Withdrawal': [25.00], 'Deposit': [None]
    }), -1, 25.00),
    (pd.DataFrame({
        'Date': ['12/07/2024'], 'Reference': ['Bank Fee'], 'Outgoing': [10.00], 'Incoming': [None]
    }), -1, 10.00),
    (pd.DataFrame({
        'Date': ['13-Jul-24'], 'Payee': ['Bookstore'], 'Amount': [-35.00]
    }), -1, 35.00),
    (pd.DataFrame({
        'Date': ['2024.07.14'], 'Particulars': ['Interest'], 'Credit': [2.50], 'Debit': [None]
    }), 1, 2.50),
    (pd.DataFrame({
        'Date': ['15/07/2024'], 'Transaction Description': ['Gym Membership'], 'Amount Debited': [50.00], 'Amount Credited': [None]
    }), -1, 50.00),
    (pd.DataFrame({
        'Date': ['16-Jul-2024'], 'Transaction Details': ['Refund'], 'CR': [75.00], 'DR': [None]
    }), 1, 75.00),
    (pd.DataFrame({
        'Date': ['17.07.2024'], 'Details': ['Cash Deposit'], 'Amount': [200.00]
    }), 1, 200.00),
    (pd.DataFrame({
        'Date': ['18/07/2024'], 'Description': ['Online Subscription'], 'Debit Amount': [15.00], 'Credit Amount': [None]
    }), -1, 15.00),
    (pd.DataFrame({
        'Date': ['19-Jul-24'], 'Narration': ['Utility Bill'], 'Withdrawals': [100.00], 'Deposits': [None]
    }), -1, 100.00),
    (pd.DataFrame({
        'Date': ['2024/07/20'], 'Memo': ['Transfer to Savings'], 'Amount': [-500.00]
    }), -1, 500.00),
    (pd.DataFrame({
        'Date': ['21-Jul-2024'], 'Description': ['Restaurant'], 'Debit': [65.00]
    }), -1, 65.00),
    (pd.DataFrame({
        'Date': ['22/07/2024'], 'Details': ['Bonus'], 'Credit': [1000.00]
    }), 1, 1000.00),
    (pd.DataFrame({
        'Date': ['23.07.2024'], 'Payee': ['Movie Tickets'], 'Amount': [-25.00]
    }), -1, 25.00)
])
def bank_statement_data(request):
    """Parameterized fixture for various bank statement formats and their expected outcomes."""
    return request.param