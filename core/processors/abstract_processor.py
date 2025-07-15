"""
Defines the abstract contract for all data processors in the application.

This module contains the core components that ensure any data processor, whether
rule-based or AI-driven, adheres to a standard interface and output schema.

Key Components:
- AbstractDataProcessor: An abstract base class that all processors must implement.
- StandardTransaction: A Pydantic model defining the required data structure for a single transaction record.
- @enforce_output_schema: A decorator that guarantees the final output DataFrame from any processor conforms to the application-wide standard.
"""

import pandas as pd
from abc import ABC, abstractmethod
from pydantic import BaseModel
from datetime import date
from functools import wraps
from typing import List

# --- Level 1: Content Validation Schema (Pydantic) ---

class StandardTransaction(BaseModel):
    """
    Pydantic model for a single, standardized transaction record.
    This is used to validate the content of data returned by processors,
    especially AI-driven ones.
    """
    description: str
    transaction_date: date
    amount: float
    category: str = "Other"
    sub_category: str = ""


# --- Level 2: Schema Enforcement (Decorator) ---

def enforce_output_schema(func):
    """
    A decorator that enforces a standard DataFrame schema on the output of a
    processor's `process_raw_data` method.

    It ensures the DataFrame has the correct columns, in the correct order,
    with the correct data types, making it safe for the DBInterface.

    Raises:
        ValueError: If the decorated function's output DataFrame cannot be
                    conformed to the standard schema.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # The standard schema expected by the DBInterface and other components.
        db_interface_columns: List[str] = [
            'description', 'amount', 'transaction_date', 'category', 'sub_category'
        ]
        
        # Call the actual processor method (e.g., AIDataProcessor.process_raw_data)
        processed_df = func(*args, **kwargs)

        if not isinstance(processed_df, pd.DataFrame):
            raise ValueError("Processor did not return a pandas DataFrame.")

        # Create a new DataFrame with the standard columns
        final_df = pd.DataFrame()
        
        # 1. Enforce Column Existence and Order
        for col in db_interface_columns:
            if col not in processed_df.columns:
                raise ValueError(f"Processed DataFrame is missing required column: '{col}'")
            final_df[col] = processed_df[col]
            
        # 2. Enforce Data Types
        try:
            final_df['transaction_date'] = pd.to_datetime(final_df['transaction_date']).dt.date
            final_df['amount'] = pd.to_numeric(final_df['amount'])
            final_df['description'] = final_df['description'].astype(str)
            final_df['category'] = final_df['category'].astype(str)
            final_df['sub_category'] = final_df['sub_category'].astype(str)
        except Exception as e:
            raise ValueError(f"Failed to enforce data types on the processed DataFrame: {e}")

        return final_df
    return wrapper


# --- Abstract Processor Contract ---

class AbstractDataProcessor(ABC):
    """
    Abstract base class for all data processors.
    
    It defines the single `process_raw_data` method that all concrete
    processor implementations (e.g., RuleBased, AI-driven) must provide.
    """
    
    @abstractmethod
    @enforce_output_schema
    def process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processes a raw DataFrame and returns a standardized DataFrame.
        
        This method is decorated with `@enforce_output_schema` to guarantee
        that the final output is always compliant with the application's
        data contract.

        Args:
            df: A raw pandas DataFrame from a file parser.

        Returns:
            A standardized pandas DataFrame with a guaranteed schema.
        """
        pass
