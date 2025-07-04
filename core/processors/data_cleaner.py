"""
Data cleaning and standardization engine for the data processor.

This module provides data cleaning capabilities including text normalization,
amount standardization, date formatting, and missing data handling for
bank statement data.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from dateutil import parser as date_parser

from .schemas import ProcessingConfig, ColumnType
from .exceptions import DataProcessorError


logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Data cleaning and standardization engine.
    
    Cleans and standardizes bank statement data including text normalization,
    amount formatting, date standardization, and missing data handling.
    """
    
    def __init__(self, config: ProcessingConfig):
        """
        Initialize the data cleaner.
        
        Args:
            config: Processing configuration with cleaning settings
        """
        self.config = config
        self._currency_symbols = ['$', '€', '£', '¥', '₹', '₽']
        self._amount_patterns = self._compile_amount_patterns()
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize a complete DataFrame.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Starting data cleaning for DataFrame with {len(df)} rows")
        
        cleaned_df = df.copy()
        
        try:
            # Clean descriptions
            if self.config.clean_descriptions and "description" in cleaned_df.columns:
                cleaned_df = self._clean_descriptions(cleaned_df)
            
            # Standardize amounts
            if self.config.standardize_amounts:
                if "amount" in cleaned_df.columns:
                    cleaned_df = self._standardize_amounts(cleaned_df, "amount")
                if "balance" in cleaned_df.columns:
                    cleaned_df = self._standardize_amounts(cleaned_df, "balance")
            
            # Standardize dates
            if "transaction_date" in cleaned_df.columns:
                cleaned_df = self._standardize_dates(cleaned_df)
            
            # Handle missing data
            if self.config.handle_missing_data:
                cleaned_df = self._handle_missing_data(cleaned_df)
            
            logger.info("Data cleaning completed successfully")
            return cleaned_df
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {str(e)}")
            raise DataProcessorError(f"Data cleaning failed: {str(e)}") from e
    
    def _clean_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize description text.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with cleaned descriptions
        """
        logger.debug("Cleaning description column")
        
        desc_col = "description"
        
        def clean_text(text):
            if pd.isna(text):
                return text
            
            # Convert to string
            text = str(text)
            
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Remove special characters but keep basic punctuation
            text = re.sub(r'[^\w\s\-\.\,\(\)\&]', '', text)
            
            # Standardize common abbreviations
            text = self._standardize_abbreviations(text)
            
            # Remove redundant words
            text = self._remove_redundant_words(text)
            
            return text
        
        df[desc_col] = df[desc_col].apply(clean_text)
        return df
    
    def _standardize_amounts(self, df: pd.DataFrame, column: str) -> pd.DataFrame:
        """
        Standardize amount formatting.
        
        Args:
            df: DataFrame to clean
            column: Amount column name
            
        Returns:
            DataFrame with standardized amounts
        """
        logger.debug(f"Standardizing {column} column")
        
        def clean_amount(value):
            if pd.isna(value):
                return value
            
            # Convert to string for processing
            amount_str = str(value).strip()
            
            # Remove currency symbols
            for symbol in self._currency_symbols:
                amount_str = amount_str.replace(symbol, '')
            
            # Remove commas used as thousand separators
            amount_str = re.sub(r',(?=\d{3})', '', amount_str)
            
            # Handle parentheses as negative indicators
            if amount_str.startswith('(') and amount_str.endswith(')'):
                amount_str = '-' + amount_str[1:-1]
            
            # Remove extra spaces
            amount_str = amount_str.strip()
            
            # Try to convert to float
            try:
                return float(amount_str)
            except ValueError:
                logger.warning(f"Could not parse amount: '{value}'")
                return value
        
        df[column] = df[column].apply(clean_amount)
        return df
    
    def _standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize date formatting to ISO format.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with standardized dates
        """
        logger.debug("Standardizing date column")
        
        date_col = "transaction_date"
        
        def clean_date(value):
            if pd.isna(value):
                return value
            
            # Try to parse the date
            parsed_date = self._parse_date(value)
            if parsed_date:
                # Return in ISO format (YYYY-MM-DD)
                return parsed_date.strftime('%Y-%m-%d')
            else:
                logger.warning(f"Could not parse date: '{value}'")
                return value
        
        df[date_col] = df[date_col].apply(clean_date)
        return df
    
    def _handle_missing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing data with appropriate defaults.
        
        Args:
            df: DataFrame to clean
            
        Returns:
            DataFrame with missing data handled
        """
        logger.debug("Handling missing data")
        
        # Handle missing descriptions
        if "description" in df.columns:
            desc_col = "description"
            df[desc_col] = df[desc_col].fillna('Unknown Transaction')
        
        # Handle missing references
        if "reference" in df.columns:
            ref_col = "reference"
            df[ref_col] = df[ref_col].fillna('')
        
        # Handle missing categories
        if "category" in df.columns:
            cat_col = "category"
            df[cat_col] = df[cat_col].fillna('Uncategorized')
        
        return df
    
    def _standardize_abbreviations(self, text: str) -> str:
        """
        Standardize common abbreviations in transaction descriptions.
        
        Args:
            text: Text to standardize
            
        Returns:
            Text with standardized abbreviations
        """
        # Common banking abbreviations
        abbreviations = {
            r'\bATM\b': 'ATM',
            r'\bPOS\b': 'POS',
            r'\bACH\b': 'ACH',
            r'\bTFR\b': 'Transfer',
            r'\bDEP\b': 'Deposit',
            r'\bWD\b': 'Withdrawal',
            r'\bCHK\b': 'Check',
            r'\bFEE\b': 'Fee',
            r'\bINT\b': 'Interest',
            r'\bDIV\b': 'Dividend',
        }
        
        for pattern, replacement in abbreviations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_redundant_words(self, text: str) -> str:
        """
        Remove redundant words from transaction descriptions.
        
        Args:
            text: Text to clean
            
        Returns:
            Text with redundant words removed
        """
        # Common redundant words in bank statements
        redundant_words = [
            'transaction', 'payment', 'purchase', 'debit', 'credit',
            'card', 'online', 'mobile', 'banking'
        ]
        
        words = text.split()
        filtered_words = []
        
        for word in words:
            if word.lower() not in redundant_words:
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    def _parse_date(self, value: Any) -> Optional[datetime]:
        """
        Parse a date value using multiple strategies.
        
        Args:
            value: Date value to parse
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        if pd.isna(value):
            return None
        
        # Convert to string if not already
        date_str = str(value).strip()
        
        # Try configured formats first
        for fmt in self.config.date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try dateutil parser as fallback
        try:
            return date_parser.parse(date_str)
        except (ValueError, TypeError):
            return None
    
    def _compile_amount_patterns(self) -> Dict[str, re.Pattern]:
        """
        Compile regex patterns for amount parsing.
        
        Returns:
            Dictionary of compiled patterns
        """
        return {
            'currency_symbols': re.compile(r'[' + ''.join(re.escape(s) for s in self._currency_symbols) + ']'),
            'thousand_separators': re.compile(r',(?=\d{3})'),
            'parentheses_negative': re.compile(r'^\((.*)\)$'),
            'whitespace': re.compile(r'\s+')
        }
    
    def get_cleaning_statistics(self, original_df: pd.DataFrame, cleaned_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate statistics about the cleaning process.
        
        Args:
            original_df: Original DataFrame before cleaning
            cleaned_df: DataFrame after cleaning
            
        Returns:
            Dictionary with cleaning statistics
        """
        stats = {
            'total_rows': len(original_df),
            'columns_cleaned': [],
            'changes_made': {}
        }
        
        # Check which columns were cleaned
        if self.config.clean_descriptions and "description" in original_df.columns:
            stats['columns_cleaned'].append("description")
            
            # Count description changes
            desc_col = "description"
            changes = (original_df[desc_col] != cleaned_df[desc_col]).sum()
            stats['changes_made'][desc_col] = changes
        
        if self.config.standardize_amounts:
            for col in ["amount", "balance"]:
                if col in original_df.columns:
                    stats['columns_cleaned'].append(col)
                    
                    # Count amount changes
                    changes = (original_df[col].astype(str) != cleaned_df[col].astype(str)).sum()
                    stats['changes_made'][col] = changes
        
        if "transaction_date" in original_df.columns:
            stats['columns_cleaned'].append("transaction_date")
            
            # Count date changes
            date_col = "transaction_date"
            changes = (original_df[date_col].astype(str) != cleaned_df[date_col].astype(str)).sum()
            stats['changes_made'][date_col] = changes
        
        return stats