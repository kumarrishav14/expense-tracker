"""
Tests for the AIDataProcessor.
"""

import pytest
import pandas as pd
from core.processors.ai_data_processor import AIDataProcessor

class TestAIDataProcessor:
    """Test suite for the AI-driven data processor."""

    def test_process_various_bank_statements(
        self,
        bank_statement_data,
        mock_db_interface,
        mock_ollama_client
    ):
        """
        Tests the processor with a wide variety of bank statement formats.
        """
        bank_statement_df, expected_sign, expected_amount = bank_statement_data
        processor = AIDataProcessor()

        categories_df = processor.db_interface.get_categories_table()
        category_hierarchy = processor._prepare_category_prompt_data(categories_df)
        prompt = processor._create_llm_prompt(data_text, category_hierarchy)
        print(f"\n{'='*50}\n[PROMPT SENT TO LLM]\n{'='*50}\n{prompt}")

        processed_df = processor.process_raw_data(bank_statement_df)

        # 1. Schema Validation
        expected_columns = {'transaction_date', 'description', 'amount', 'category', 'sub_category'}
        assert set(processed_df.columns) == expected_columns

        # 2. Amount and Sign Validation
        assert len(processed_df) > 0, "Processor returned an empty DataFrame"
        actual_amount = processed_df['amount'].iloc[0]
        assert abs(actual_amount) == expected_amount
        assert (actual_amount > 0) == (expected_sign > 0) or (actual_amount < 0) == (expected_sign < 0)

        # 3. The following assertions will pass once the decorator is correctly applied.                        
        assert pd.api.types.is_datetime64_any_dtype(processed_df['transaction_date'])                          
        assert pd.api.types.is_numeric_dtype(processed_df['amount'])                                           
        assert pd.api.types.is_string_dtype(processed_df['description'])                                
        assert pd.api.types.is_string_dtype(processed_df['category'])