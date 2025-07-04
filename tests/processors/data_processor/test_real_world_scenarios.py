"""
Real-world scenario tests for DataProcessor component.

This module tests DataProcessor with realistic personal banking scenarios
and actual bank statement formats.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from core.processors.data_processor import DataProcessor


class TestRealWorldScenarios:
    """Test cases for real-world personal banking scenarios."""

    def test_monthly_bank_statement_processing(self, data_processor):
        """Test processing a complete monthly bank statement."""
        # Simulate a realistic monthly bank statement
        monthly_statement = pd.DataFrame({
            'Transaction Date': [
                '01/01/2024', '01/02/2024', '01/03/2024', '01/05/2024',
                '01/07/2024', '01/10/2024', '01/12/2024', '01/15/2024',
                '01/18/2024', '01/20/2024', '01/22/2024', '01/25/2024',
                '01/28/2024', '01/30/2024'
            ],
            'Description': [
                'SALARY DEPOSIT COMPANY ABC',
                'GROCERY STORE SAFEWAY #123',
                'STARBUCKS COFFEE #456',
                'SHELL GAS STATION #789',
                'RESTAURANT CHIPOTLE #101',
                'AMAZON.COM PURCHASE',
                'NETFLIX SUBSCRIPTION',
                'ATM WITHDRAWAL BANK OF AMERICA',
                'UTILITY BILL PG&E',
                'PHONE BILL VERIZON',
                'GROCERY STORE WHOLE FOODS',
                'RESTAURANT OLIVE GARDEN',
                'GAS STATION CHEVRON #234',
                'ONLINE PURCHASE EBAY'
            ],
            'Amount': [
                '2500.00', '-85.32', '-5.50', '-45.67', '-28.50',
                '-125.75', '-12.99', '-100.00', '-85.30', '-65.00',
                '-92.45', '-67.89', '-42.33', '-78.90'
            ],
            'Balance': [
                '3500.00', '3414.68', '3409.18', '3363.51', '3335.01',
                '3209.26', '3196.27', '3096.27', '3010.97', '2945.97',
                '2853.52', '2785.63', '2743.30', '2664.40'
            ]
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(monthly_statement)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 14
        
        # Should have all essential columns
        essential_columns = ['date', 'description', 'amount']
        for col in essential_columns:
            assert col in processed_df.columns

    def test_credit_card_statement_processing(self, data_processor):
        """Test processing a credit card statement."""
        credit_card_statement = pd.DataFrame({
            'Trans. Date': [
                '01/05/2024', '01/07/2024', '01/10/2024', '01/12/2024',
                '01/15/2024', '01/18/2024', '01/20/2024', '01/22/2024'
            ],
            'Description': [
                'AMAZON.COM PURCHASE',
                'UBER RIDE SERVICE',
                'SPOTIFY SUBSCRIPTION',
                'RESTAURANT DINNER',
                'ONLINE SHOPPING TARGET',
                'GAS STATION PURCHASE',
                'GROCERY DELIVERY',
                'MOVIE THEATER TICKETS'
            ],
            'Amount': [
                '$125.75', '$18.50', '$9.99', '$67.89',
                '$89.45', '$42.33', '$78.90', '$24.50'
            ],
            'Category': [
                'Shopping', 'Transportation', 'Entertainment', 'Food & Dining',
                'Shopping', 'Transportation', 'Groceries', 'Entertainment'
            ]
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(credit_card_statement)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 8

    def test_mixed_transaction_types_processing(self, data_processor):
        """Test processing mixed transaction types (debits, credits, transfers)."""
        mixed_transactions = pd.DataFrame({
            'Date': [
                '01/01/2024', '01/02/2024', '01/03/2024', '01/05/2024',
                '01/07/2024', '01/10/2024', '01/12/2024', '01/15/2024'
            ],
            'Description': [
                'DIRECT DEPOSIT SALARY',
                'DEBIT CARD PURCHASE GROCERY',
                'ONLINE TRANSFER TO SAVINGS',
                'CHECK DEPOSIT #1234',
                'ATM WITHDRAWAL',
                'AUTOMATIC PAYMENT UTILITIES',
                'WIRE TRANSFER RECEIVED',
                'MOBILE PAYMENT VENMO'
            ],
            'Debit': [
                '', '85.32', '500.00', '', '100.00', '125.50', '', '25.00'
            ],
            'Credit': [
                '2500.00', '', '', '150.00', '', '', '300.00', ''
            ],
            'Balance': [
                '3500.00', '3414.68', '2914.68', '3064.68',
                '2964.68', '2839.18', '3139.18', '3114.18'
            ]
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(mixed_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 8

    def test_international_transactions_processing(self, data_processor):
        """Test processing international transactions with different currencies."""
        international_transactions = pd.DataFrame({
            'Date': ['01/15/2024', '01/16/2024', '01/17/2024', '01/18/2024'],
            'Description': [
                'FOREIGN TRANSACTION LONDON UK',
                'CURRENCY EXCHANGE FEE',
                'INTERNATIONAL ATM WITHDRAWAL',
                'OVERSEAS PURCHASE PARIS FR'
            ],
            'Amount': ['-$125.75', '-$3.50', '-$105.00', '-$89.45'],
            'Balance': ['2500.00', '2496.50', '2391.50', '2302.05'],
            'Currency': ['USD', 'USD', 'USD', 'USD']
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(international_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 4

    def test_recurring_transactions_processing(self, data_processor):
        """Test processing recurring transactions (subscriptions, bills)."""
        recurring_transactions = pd.DataFrame({
            'Date': [
                '01/01/2024', '01/05/2024', '01/10/2024', '01/15/2024',
                '01/20/2024', '01/25/2024', '01/30/2024'
            ],
            'Description': [
                'NETFLIX SUBSCRIPTION RECURRING',
                'SPOTIFY PREMIUM MONTHLY',
                'UTILITY BILL AUTO-PAY PG&E',
                'PHONE BILL AUTO-PAY VERIZON',
                'INSURANCE PREMIUM AUTO-PAY',
                'MORTGAGE PAYMENT AUTO-PAY',
                'CREDIT CARD PAYMENT AUTO-PAY'
            ],
            'Amount': [
                '-$12.99', '-$9.99', '-$85.30', '-$65.00',
                '-$125.50', '-$1850.00', '-$250.00'
            ],
            'Balance': [
                '2987.01', '2977.02', '2891.72', '2826.72',
                '2701.22', '851.22', '601.22'
            ]
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(recurring_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 7

    def test_business_expense_processing(self, data_processor):
        """Test processing business-related expenses."""
        business_expenses = pd.DataFrame({
            'Transaction Date': [
                '01/05/2024', '01/08/2024', '01/12/2024', '01/15/2024',
                '01/18/2024', '01/22/2024', '01/25/2024'
            ],
            'Description': [
                'OFFICE SUPPLIES STAPLES',
                'BUSINESS LUNCH RESTAURANT',
                'SOFTWARE SUBSCRIPTION ADOBE',
                'TRAVEL EXPENSE HOTEL',
                'CONFERENCE REGISTRATION FEE',
                'BUSINESS MILEAGE REIMBURSEMENT',
                'CLIENT DINNER EXPENSE'
            ],
            'Amount': [
                '-$45.67', '-$78.90', '-$29.99', '-$185.50',
                '-$299.00', '+$125.50', '-$156.75'
            ],
            'Balance': [
                '1954.33', '1875.43', '1845.44', '1659.94',
                '1360.94', '1486.44', '1329.69'
            ]
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(business_expenses)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 7

    def test_investment_transactions_processing(self, data_processor):
        """Test processing investment-related transactions."""
        investment_transactions = pd.DataFrame({
            'Date': ['01/10/2024', '01/15/2024', '01/20/2024', '01/25/2024'],
            'Description': [
                'TRANSFER TO INVESTMENT ACCOUNT',
                'DIVIDEND PAYMENT RECEIVED',
                'STOCK PURCHASE COMMISSION',
                'RETIREMENT CONTRIBUTION 401K'
            ],
            'Amount': ['-$1000.00', '+$45.75', '-$9.95', '-$500.00'],
            'Balance': ['4000.00', '4045.75', '4035.80', '3535.80']
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(investment_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 4

    def test_cash_transactions_processing(self, data_processor):
        """Test processing manually entered cash transactions."""
        cash_transactions = pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18'],
            'description': [
                'Cash grocery shopping farmers market',
                'Coffee shop tip cash',
                'Parking meter cash payment',
                'Street vendor lunch cash'
            ],
            'amount': [35.00, 2.50, 3.00, 8.50],
            'category': ['Groceries', 'Food & Dining', 'Transportation', 'Food & Dining'],
            'notes': ['Weekly farmers market', 'Local coffee shop', 'Downtown parking', 'Food truck']
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(cash_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 4

    def test_year_end_processing(self, data_processor):
        """Test processing year-end financial transactions."""
        year_end_transactions = pd.DataFrame({
            'Date': [
                '12/28/2023', '12/29/2023', '12/30/2023', '12/31/2023',
                '01/01/2024', '01/02/2024'
            ],
            'Description': [
                'YEAR END BONUS DEPOSIT',
                'CHARITY DONATION TAX DEDUCTIBLE',
                'INVESTMENT CONTRIBUTION IRA',
                'BANK FEE YEAR END STATEMENT',
                'NEW YEAR INTEREST PAYMENT',
                'FIRST TRANSACTION NEW YEAR'
            ],
            'Amount': [
                '+$5000.00', '-$500.00', '-$2000.00', '-$25.00',
                '+$12.50', '-$45.67'
            ],
            'Balance': [
                '8000.00', '7500.00', '5500.00', '5475.00',
                '5487.50', '5441.83'
            ]
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(year_end_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 6

    def test_multi_account_processing(self, data_processor):
        """Test processing transactions from multiple accounts."""
        checking_account = pd.DataFrame({
            'Date': ['01/15/2024', '01/16/2024'],
            'Description': ['CHECKING ACCOUNT PURCHASE', 'CHECKING ACCOUNT DEPOSIT'],
            'Amount': ['-$50.00', '+$200.00'],
            'Balance': ['1950.00', '2150.00'],
            'Account': ['Checking', 'Checking']
        })
        
        savings_account = pd.DataFrame({
            'Date': ['01/15/2024', '01/16/2024'],
            'Description': ['SAVINGS ACCOUNT INTEREST', 'SAVINGS ACCOUNT TRANSFER'],
            'Amount': ['+$5.50', '-$100.00'],
            'Balance': ['5005.50', '4905.50'],
            'Account': ['Savings', 'Savings']
        })
        
        # Test each account separately
        checking_processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(checking_account)
        savings_processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(savings_account)
        
        assert checking_result is not None
        assert savings_result is not None
        assert isinstance(checking_result, pd.DataFrame)
        assert isinstance(savings_result, pd.DataFrame)

    def test_large_purchase_processing(self, data_processor):
        """Test processing large purchases (car, house down payment, etc.)."""
        large_purchases = pd.DataFrame({
            'Date': ['01/15/2024', '01/16/2024', '01/17/2024'],
            'Description': [
                'CAR PURCHASE DOWN PAYMENT',
                'HOME DOWN PAYMENT WIRE TRANSFER',
                'LARGE APPLIANCE PURCHASE'
            ],
            'Amount': ['-$5000.00', '-$50000.00', '-$2500.00'],
            'Balance': ['45000.00', '-5000.00', '-7500.00']
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(large_purchases)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 3

    def test_refund_and_return_processing(self, data_processor):
        """Test processing refunds and returns."""
        refund_transactions = pd.DataFrame({
            'Date': [
                '01/10/2024', '01/12/2024', '01/15/2024', '01/18/2024'
            ],
            'Description': [
                'ORIGINAL PURCHASE AMAZON',
                'REFUND AMAZON RETURN',
                'RESTAURANT CHARGE',
                'RESTAURANT REFUND DISPUTE'
            ],
            'Amount': ['-$125.75', '+$125.75', '-$67.89', '+$67.89'],
            'Balance': ['1874.25', '2000.00', '1932.11', '2000.00']
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(refund_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 4

    def test_fee_and_charge_processing(self, data_processor):
        """Test processing various fees and charges."""
        fee_transactions = pd.DataFrame({
            'Date': [
                '01/15/2024', '01/16/2024', '01/17/2024', '01/18/2024'
            ],
            'Description': [
                'OVERDRAFT FEE',
                'ATM FEE OUT OF NETWORK',
                'FOREIGN TRANSACTION FEE',
                'MONTHLY MAINTENANCE FEE'
            ],
            'Amount': ['-$35.00', '-$3.50', '-$2.75', '-$12.00'],
            'Balance': ['1965.00', '1961.50', '1958.75', '1946.75']
        })
        
        processed_df, processing_processed_df, processing_result = data_processor.process_dataframe(fee_transactions)
        
        assert processed_df is not None
        assert isinstance(processed_df, pd.DataFrame)
        assert len(processed_df) == 4