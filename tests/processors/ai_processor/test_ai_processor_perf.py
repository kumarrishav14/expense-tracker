"""
Performance tests for the AIDataProcessor.
"""

import pytest
import pandas as pd
import time
import random
import datetime
from core.processors.ai_data_processor import AIDataProcessor


@pytest.fixture(params=[
    # Dataset 1: Standard columns with realistic descriptions
    # pd.DataFrame({
    #     'Date': [f'2024-07-{i+1:02d}' for i in range(50)],
    #     'Description': random.choices([
    #         'Amazon Prime Video', 'Spotify Subscription', 'Tesco Groceries',
    #         'Shell Gas Station', 'Starbucks Coffee', 'Netflix',
    #         'H&M Clothing', 'Uber Ride', 'Deliveroo',
    #         'British Gas Bill', 'Council Tax', 'Salary Deposit',
    #         'ATM Withdrawal', 'Online Transfer to John Doe', 'Apple Store',
    #         'Boots Pharmacy', 'EasyJet Flights', 'Cinema Tickets',
    #         'Waterstones Books', 'Gym Membership'
    #     ], k=50),
    #     'Amount': [round(random.uniform(-200, 200), 2) for _ in range(50)]
    # }),
    # # Dataset 2: Different column names with realistic descriptions
    # pd.DataFrame({
    #     'Transaction Date': [f'07/{i+1:02d}/2024' for i in range(50)],
    #     'Details': random.choices([
    #         'POS Purchase at Target', 'ACH Deposit from Work', 'BBP to AT&T',
    #         'CHK #1234 to Landlord', 'EFT to Savings', 'INT Earned',
    #         'TFR from Checking', 'UPI to Merchant', 'Monthly Fee',
    #         'Zelle to Jane Smith', 'Costco Wholesale', 'Whole Foods Market',
    #         'Chevron Gas', 'Comcast Bill', 'Direct Deposit',
    #         'Chase QuickPay', 'Venmo to Friend', 'Bank of America ATM',
    #         'Mortgage Payment', 'Car Loan Payment'
    #     ], k=50),
    #     'Debit': [round(random.uniform(5, 300), 2) if i % 2 != 0 else None for i in range(50)],
    #     'Credit': [round(random.uniform(100, 2000), 2) if i % 2 == 0 else None for i in range(50)]
    # }),
    # Dataset 3: Indian bank statement format
    pd.DataFrame({
        'Date': [(datetime.date(2024, 6, 1) + datetime.timedelta(days=random.randint(0, 59))).strftime('%d-%m-%Y') for _ in range(50)],
        'Narration': random.choices([
            'UPI/PAYTM/TRANSFER', 'NEFT/TRANSFER/JOHN', 'IMPS/FOOD/ZOMATO',
            'ATM/WDL/MUMBAI', 'BIL/PAY/VODAFONE', 'ECS/SIP/MUTUALFUND',
            'CLG/CHQ/001234', 'INFT/SALARY/CREDIT', 'POS/PURCHASE/RELIANCE',
            'RTGS/TRANSFER/ACME', 'BBPS/BILL/ELECTRICITY', 'EBA/TRADE/ZERODHA',
            'FD/INTEREST/CREDIT', 'GST/PAYMENT/JULY', 'RCHG/MOBILE/AIRTEL',
            'N-CHG/NEFT/FEE', 'MMT/PAY/GROCERIES', 'PAVC/CREDITCARD/BILL',
            'DTAX/PAYMENT/2024', 'IRM/REMIT/USA'
        ], k=50),
        'Debit': [round(random.uniform(100, 5000), 2) if i % 2 != 0 else None for i in range(50)],
        'Credit': [round(random.uniform(5000, 50000), 2) if i % 2 == 0 else None for i in range(50)]
    })
])
def large_bank_statement_data(request):
    """Parameterized fixture for large bank statement DataFrames (50 rows) with realistic data."""
    return request.param


class TestAIDataProcessorPerformance:
    """Performance test suite for the AI-driven data processor."""

    def test_process_large_statement_performance(
        self,
        large_bank_statement_data,
        mock_db_interface
    ):
        """
        Tests the performance of the processor with a large number of transactions.
        """
        processor = AIDataProcessor()

        def progress_callback(progress: float, message: str):
            """Callback to print progress updates."""
            print(f"Progress: {progress*100:.2f}% - {message}")
        
        start_time = time.time()
        processed_df = processor.process_raw_data(
            large_bank_statement_data,
            on_progress=progress_callback
        )
        end_time = time.time()

        processing_time = end_time - start_time
        print(f"Processing time for 50 records: {processing_time:.2f} seconds")

        # 1. Schema Validation
        expected_columns = {'transaction_date', 'description', 'amount', 'category', 'sub_category'}
        assert set(processed_df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, but got {set(processed_df.columns)}"

        # 2. Row Count Validation with detailed mismatch reporting
        if len(processed_df) != len(large_bank_statement_data):
            input_desc_col = None
            if 'Description' in large_bank_statement_data.columns:
                input_desc_col = 'Description'
            elif 'Details' in large_bank_statement_data.columns:
                input_desc_col = 'Details'
            elif 'Narration' in large_bank_statement_data.columns:
                input_desc_col = 'Narration'

            if input_desc_col:
                input_descriptions = set(large_bank_statement_data[input_desc_col])
                output_descriptions = set(processed_df['description'])
                missing_descriptions = input_descriptions - output_descriptions
                
                missing_rows = large_bank_statement_data[
                    large_bank_statement_data[input_desc_col].isin(missing_descriptions)
                ]
                
                error_message = (
                    f"Row count mismatch. Expected {len(large_bank_statement_data)}, got {len(processed_df)}.\n"
                    f"Missing rows from input:\n{missing_rows.to_string()}"
                )
                pytest.fail(error_message)
            else:
                pytest.fail(
                    f"Row count mismatch and could not find a description column to compare. "
                    f"Expected {len(large_bank_statement_data)}, got {len(processed_df)}."
                )

        # 3. Performance Assertion (e.g., assert processing time is under 30 seconds)
        # This threshold can be adjusted based on the expected performance.
        assert processing_time < 120, f"Processing time ({processing_time:.2f}s) exceeded the 120s (2min) threshold."