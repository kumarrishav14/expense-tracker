"""
Rule-Based Data Processor with AI Fallback

This module provides a concrete implementation of the AbstractDataProcessor.
It attempts to use an AI for categorization first, and falls back to a simple
rule-based approach if the AI service is unavailable.
"""

import pandas as pd
from typing import Optional

from .abstract_processor import AbstractDataProcessor
from ai.ollama.client import OllamaClient
from ai.ollama.factory import get_ollama_client, is_ollama_available

class RuleBasedDataProcessor(AbstractDataProcessor):
    """
    A processor that uses AI for categorization with a rule-based fallback.
    It adheres to the contract defined by AbstractDataProcessor.
    """
    
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initializes the processor, checking for AI service availability.
        """
        # Simple column mapping patterns
        self.column_mappings = {
            'transaction_date': ['date', 'transaction_date', 'trans_date', 'posting_date', 'value_date', 'transaction date'],
            'description': ['description', 'details', 'transaction_details', 'narration', 'particulars', 'transaction details'],
            'amount': ['amount', 'transaction_amount', 'value', 'transaction amount'],
        }
        
        # Simple category rules for fallback categorization
        self.category_rules = {
            'Food & Dining': ['restaurant', 'food', 'cafe', 'dining', 'swiggy', 'zomato', 'uber eats'],
            'Transportation': ['uber', 'ola', 'metro', 'bus', 'taxi', 'fuel', 'petrol', 'diesel'],
            'Shopping': ['amazon', 'flipkart', 'mall', 'store', 'shopping', 'purchase'],
            'Bills & Utilities': ['electricity', 'water', 'gas', 'internet', 'mobile', 'phone'],
            'Healthcare': ['hospital', 'clinic', 'pharmacy', 'medical', 'doctor'],
            'Entertainment': ['movie', 'cinema', 'netflix', 'spotify', 'game'],
            'Transfer': ['transfer', 'neft', 'rtgs', 'imps', 'upi'],
            'ATM': ['atm', 'cash withdrawal'],
            'Salary': ['salary', 'wages', 'income'],
            'Other': []
        }

        # AI Client Initialization
        if ollama_client:
            self.ollama_client = ollama_client
            self.ollama_enabled = self.ollama_client.test_connection()
        else:
            self.ollama_enabled = is_ollama_available()
            self.ollama_client = get_ollama_client() if self.ollama_enabled else None

    def process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main processing method that orchestrates the data transformation pipeline.
        The @enforce_output_schema decorator is inherited from the parent class.
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        
        mapped_df = self._map_columns(df)
        cleaned_df = self._validate_and_clean_data(mapped_df)
        categorized_df = self._add_categories(cleaned_df)
        
        return categorized_df

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Maps raw DataFrame columns to the standard schema.
        """
        mapped_df = df.copy()
        column_map = {}
        
        df_columns_lower = [str(col).lower().strip() for col in df.columns]
        
        for standard_col, possible_names in self.column_mappings.items():
            for possible_name in possible_names:
                if possible_name.lower() in df_columns_lower:
                    original_col = df.columns[df_columns_lower.index(possible_name.lower())]
                    column_map[original_col] = standard_col
                    break
        
        mapped_df = mapped_df.rename(columns=column_map)
        
        if 'amount' not in mapped_df.columns:
            debit_col, credit_col = None, None
            for col in mapped_df.columns:
                if str(col).lower() in ['debit', 'debit_amount']:
                    debit_col = col
                elif str(col).lower() in ['credit', 'credit_amount']:
                    credit_col = col
            
            if debit_col and credit_col:
                mapped_df['amount'] = pd.to_numeric(mapped_df[credit_col], errors='coerce').fillna(0) - \
                                      pd.to_numeric(mapped_df[debit_col], errors='coerce').fillna(0)
                mapped_df = mapped_df.drop(columns=[debit_col, credit_col])
        
        required_cols = {'transaction_date', 'description', 'amount'}
        if not required_cols.issubset(mapped_df.columns):
            missing = required_cols - set(mapped_df.columns)
            raise ValueError(f"Cannot map required columns: {missing}")
        
        for col in ['category', 'sub_category']:
            if col not in mapped_df.columns:
                mapped_df[col] = ""
        
        return mapped_df

    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Performs basic data validation and cleaning.
        """
        cleaned_df = df.copy()
        
        cleaned_df['transaction_date'] = pd.to_datetime(cleaned_df['transaction_date'], errors='coerce')
        cleaned_df = cleaned_df.dropna(subset=['transaction_date'])
        
        if cleaned_df['amount'].dtype == 'object':
            cleaned_df['amount'] = cleaned_df['amount'].astype(str).str.replace(r'[Rs$,\s]', '', regex=True)
        cleaned_df['amount'] = pd.to_numeric(cleaned_df['amount'], errors='coerce')
        cleaned_df = cleaned_df.dropna(subset=['amount'])
        
        cleaned_df['description'] = cleaned_df['description'].astype(str).str.strip()
        cleaned_df = cleaned_df[cleaned_df['description'].str.len() > 0]
        
        cleaned_df = cleaned_df.drop_duplicates(subset=['transaction_date', 'amount', 'description'])
        
        if cleaned_df.empty:
            raise ValueError("All rows were removed during data cleaning")
        
        return cleaned_df

    def _add_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Categorizes transactions using AI, with a rule-based fallback.
        """
        categorized_df = df.copy()
        
        if 'category' not in categorized_df.columns:
            categorized_df['category'] = ""
        if 'sub_category' not in categorized_df.columns:
            categorized_df['sub_category'] = ""

        available_categories = list(self.category_rules.keys())

        if self.ollama_enabled and self.ollama_client:
            for idx, row in categorized_df.iterrows():
                if pd.notna(row['category']) and row['category'].strip():
                    continue
                description = str(row['description'])
                predicted_category = self.ollama_client.categorize_transaction(
                    transaction_description=description,
                    available_categories=available_categories
                )
                categorized_df.at[idx, 'category'] = predicted_category
        else:
            for idx, row in categorized_df.iterrows():
                if pd.notna(row['category']) and row['category'].strip():
                    continue
                description = str(row['description']).lower()
                assigned_category = 'Other'
                for category, keywords in self.category_rules.items():
                    if any(keyword.lower() in description for keyword in keywords):
                        assigned_category = category
                        break
                categorized_df.at[idx, 'category'] = assigned_category
        
        return categorized_df
