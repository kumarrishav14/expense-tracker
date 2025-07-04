"""
Simplified Data Processor Implementation

Single-class implementation that converts raw bank statement data into 
standardized DataFrames compatible with db_interface. Follows the approved
micro-architecture with 4 simple methods.

This replaces the over-engineered multi-component system with a focused,
maintainable solution appropriate for a personal expense tracking app.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re


class DataProcessor:
    """
    Simplified data processor for converting raw bank statement data 
    into standardized DataFrames compatible with db_interface.
    
    This class handles:
    - Intelligent column mapping from raw data to standard schema
    - Basic data validation and cleaning
    - Simple AI-powered categorization
    - Format standardization for database persistence
    
    Output DataFrame matches db_interface expectations:
    - description: str (transaction description)
    - amount: float (transaction amount) 
    - transaction_date: datetime (when transaction occurred)
    - category: str (main category name)
    - sub_category: str (sub-category name)
    
    Note: created_at and updated_at are handled internally by db_interface
    """
    
    def __init__(self):
        """Initialize the data processor with standard column mappings."""
        # Standard column names expected by db_interface (from architecture spec)
        self.db_interface_columns = [
            'description', 'amount', 'transaction_date', 'category', 'sub_category'
        ]
        
        # Simple column mapping patterns for common bank statement formats
        self.column_mappings = {
            'transaction_date': ['date', 'transaction_date', 'trans_date', 'posting_date', 'value_date', 'transaction date'],
            'description': ['description', 'details', 'transaction_details', 'narration', 'particulars', 'transaction details'],
            'amount': ['amount', 'transaction_amount', 'debit', 'credit', 'value', 'transaction amount'],
            'category': ['category', 'type', 'transaction_type'],
            'sub_category': ['sub_category', 'subcategory', 'sub_type']
        }
        
        # Simple category rules for basic AI categorization
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
            'Other': []  # Default category
        }

    def process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Main processing method that orchestrates the entire data transformation pipeline.
        
        Args:
            df: Raw pandas DataFrame from file parsers with any column structure
            
        Returns:
            Standardized DataFrame compatible with db_interface
            
        Raises:
            ValueError: If input DataFrame is empty or has no valid columns
        """
        if df.empty:
            raise ValueError("Input DataFrame is empty")
        
        # Step 1: Map columns to standard schema
        mapped_df = self.map_columns(df)
        
        # Step 2: Validate and clean the data
        cleaned_df = self.validate_and_clean_data(mapped_df)
        
        # Step 3: Add AI-powered categories
        categorized_df = self.add_ai_categories(cleaned_df)
        
        # Step 4: Ensure only db_interface expected columns are present
        # Note: created_at and updated_at are handled internally by db_interface
        final_df = categorized_df[self.db_interface_columns].copy()
        
        return final_df

    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Simple column mapping from raw DataFrame to standard schema.
        
        Uses fuzzy string matching to map common bank statement column names
        to the standard schema expected by db_interface.
        
        Args:
            df: Raw DataFrame with any column names
            
        Returns:
            DataFrame with columns mapped to standard schema
            
        Raises:
            ValueError: If required columns (transaction_date, description, amount) cannot be mapped
        """
        mapped_df = df.copy()
        column_map = {}
        
        # Convert column names to lowercase for case-insensitive matching
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        # Map each standard column to the best matching raw column
        for standard_col, possible_names in self.column_mappings.items():
            best_match = None
            
            # Look for exact matches first
            for possible_name in possible_names:
                if possible_name.lower() in df_columns_lower:
                    original_col = df.columns[df_columns_lower.index(possible_name.lower())]
                    best_match = original_col
                    break
            
            # If exact match found, add to mapping
            if best_match:
                column_map[best_match] = standard_col
        
        # Rename columns according to mapping
        mapped_df = mapped_df.rename(columns=column_map)
        
        # Handle debit/credit columns - combine them into amount
        if 'amount' not in mapped_df.columns:
            debit_col = None
            credit_col = None
            
            # Look for debit/credit columns
            for col in mapped_df.columns:
                if col.lower() in ['debit', 'debit_amount']:
                    debit_col = col
                elif col.lower() in ['credit', 'credit_amount']:
                    credit_col = col
            
            if debit_col is not None and credit_col is not None:
                # Combine debit and credit: credit is positive, debit is negative
                mapped_df['amount'] = mapped_df[credit_col].fillna(0) - mapped_df[debit_col].fillna(0)
                # Drop the original debit/credit columns
                mapped_df = mapped_df.drop(columns=[debit_col, credit_col])
        
        # Check if we have the required columns
        mapped_standard_cols = set(mapped_df.columns) & set(self.column_mappings.keys())
        required_cols = {'transaction_date', 'description', 'amount'}
        missing_required = required_cols - mapped_standard_cols
        
        if missing_required:
            raise ValueError(f"Cannot map required columns: {missing_required}. "
                           f"Available columns: {list(df.columns)}")
        
        # Add missing optional columns with default values
        for col in self.db_interface_columns:
            if col not in mapped_df.columns:
                if col in ['category', 'sub_category']:
                    mapped_df[col] = None
        
        return mapped_df

    def validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Basic data validation and cleaning operations.
        
        Performs simple data quality checks and standardizes formats:
        - Converts date columns to datetime
        - Ensures amount is numeric
        - Cleans description text
        - Removes invalid rows
        
        Args:
            df: DataFrame with mapped columns
            
        Returns:
            Cleaned and validated DataFrame
            
        Raises:
            ValueError: If data cleaning fails or results in empty DataFrame
        """
        cleaned_df = df.copy()
        
        # Clean and validate transaction_date column
        try:
            cleaned_df['transaction_date'] = pd.to_datetime(cleaned_df['transaction_date'], errors='coerce')
            # Remove rows with invalid dates
            cleaned_df = cleaned_df.dropna(subset=['transaction_date'])
        except Exception as e:
            raise ValueError(f"Failed to parse transaction_date column: {e}")
        
        # Clean and validate amount column
        try:
            # Handle string amounts (remove currency symbols, commas)
            if cleaned_df['amount'].dtype == 'object':
                cleaned_df['amount'] = cleaned_df['amount'].astype(str)
                # Remove currency symbols and commas
                cleaned_df['amount'] = cleaned_df['amount'].str.replace(r'[Rs,$,\s]', '', regex=True)
                cleaned_df['amount'] = cleaned_df['amount'].str.replace(',', '')
            
            cleaned_df['amount'] = pd.to_numeric(cleaned_df['amount'], errors='coerce')
            # Remove rows with invalid amounts
            cleaned_df = cleaned_df.dropna(subset=['amount'])
        except Exception as e:
            raise ValueError(f"Failed to parse amount column: {e}")
        
        # Clean description column
        if 'description' in cleaned_df.columns:
            cleaned_df['description'] = cleaned_df['description'].astype(str)
            cleaned_df['description'] = cleaned_df['description'].str.strip()
            # Remove rows with empty descriptions
            cleaned_df = cleaned_df[cleaned_df['description'].str.len() > 0]
        
        # Remove duplicate transactions (same date, amount, description)
        cleaned_df = cleaned_df.drop_duplicates(subset=['transaction_date', 'amount', 'description'])
        
        if cleaned_df.empty:
            raise ValueError("All rows were removed during data cleaning")
        
        return cleaned_df

    #TODO: Replace with actual AI categorization logic once the AI backend is up.
    def add_ai_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Simple rule-based categorization for transactions.
        
        Uses keyword matching to assign categories to transactions based on
        description text. This is a simplified version of AI categorization.
        
        Args:
            df: Cleaned DataFrame with valid transactions
            
        Returns:
            DataFrame with category and sub_category columns populated
        """
        categorized_df = df.copy()
        
        # Initialize category columns if they don't exist
        if 'category' not in categorized_df.columns:
            categorized_df['category'] = None
        if 'sub_category' not in categorized_df.columns:
            categorized_df['sub_category'] = None
        
        # Apply rule-based categorization
        for idx, row in categorized_df.iterrows():
            # Skip if category is already assigned
            if pd.notna(row['category']) and row['category'].strip():
                continue
            
            description = str(row['description']).lower()
            assigned_category = 'Other'  # Default category
            
            # Check each category rule
            for category, keywords in self.category_rules.items():
                if category == 'Other':
                    continue
                
                # Check if any keyword matches the description
                for keyword in keywords:
                    if keyword.lower() in description:
                        assigned_category = category
                        break
                
                if assigned_category != 'Other':
                    break
            
            categorized_df.at[idx, 'category'] = assigned_category
            
            # Simple sub-category assignment based on amount
            amount = abs(float(row['amount']))
            if amount > 10000:
                categorized_df.at[idx, 'sub_category'] = 'Large Transaction'
            elif amount < 100:
                categorized_df.at[idx, 'sub_category'] = 'Small Transaction'
            else:
                categorized_df.at[idx, 'sub_category'] = 'Regular Transaction'
        
        return categorized_df

    def get_processing_summary(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> Dict:
        """
        Generate a simple summary of the processing results.
        
        Args:
            original_df: Original raw DataFrame
            processed_df: Final processed DataFrame
            
        Returns:
            Dictionary with processing statistics
        """
        return {
            'original_rows': len(original_df),
            'processed_rows': len(processed_df),
            'rows_removed': len(original_df) - len(processed_df),
            'categories_assigned': len(processed_df[processed_df['category'].notna()]),
            'processing_success': True
        }