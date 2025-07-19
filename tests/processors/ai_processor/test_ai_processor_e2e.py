"""
End-to-end tests for the AIDataProcessor.
"""

import pytest
import pandas as pd
from core.processors.ai_data_processor import AIDataProcessor

class TestAIDataProcessorE2E:
    """Test suite for the AI-driven data processor (end-to-end)."""

    def test_process_various_bank_statements_e2e(
        self,
        bank_statement_data,
        mock_db_interface
    ):
        """
        Tests the processor with a wide variety of bank statement formats using a real LLM.
        """
        bank_statement_df, expected_sign, expected_amount = bank_statement_data
        processor = AIDataProcessor()
        processed_df = processor.process_raw_data(bank_statement_df)

        # 1. Schema Validation
        expected_columns = {'transaction_date', 'description', 'amount', 'category', 'sub_category'}
        assert set(processed_df.columns) == expected_columns, \
            f"Expected columns {expected_columns}, but got {set(processed_df.columns)}"

        # 2. Amount and Sign Validation
        assert len(processed_df) == 1, f"Processor returned {len(processed_df)} rows, expected 1"
        actual_amount = processed_df['amount'].iloc[0]
        assert abs(actual_amount) == expected_amount, \
            f"Expected amount {expected_amount}, but got {actual_amount}"
        assert (actual_amount > 0) == (expected_sign > 0) or (actual_amount < 0) == (expected_sign < 0), \
            f"Expected sign {expected_sign}, but got amount {actual_amount}"

        # 3. Data Type Validation
        assert pd.api.types.is_datetime64_any_dtype(processed_df['transaction_date']), \
            "'transaction_date' column should be of datetime type"
        assert pd.api.types.is_numeric_dtype(processed_df['amount']), \
            "'amount' column should be of numeric type"
        assert pd.api.types.is_string_dtype(processed_df['description']), \
            "'description' column should be of string type"
        assert pd.api.types.is_string_dtype(processed_df['category']), \
            "'category' column should be of string type"