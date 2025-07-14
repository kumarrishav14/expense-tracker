"""
CSV Parser for Bank Statements

This module provides a simple and robust parser for converting CSV files 
from financial institutions into a standardized pandas DataFrame.

It is designed to handle common CSV format variations, including:
- Different delimiters (comma, semicolon)
- Various header and footer rows
- Flexible encoding to prevent common import errors
"""

import pandas as pd
import io
from typing import Union, IO

class CSVParser:
    """
    A robust parser for converting CSV files into pandas DataFrames.
    
    This class encapsulates the logic for reading and cleaning CSV files,
    making it easy to load financial data from various sources.
    """
    
    def __init__(self, file_source: Union[str, io.BytesIO], encoding: str = 'utf-8'):
        """
        Initialize the parser with the path to the CSV file.
        
        Args:
            file_source: The full path to the CSV file or a file-like object.
            encoding: The character encoding of the file.
        """
        self.file_source = file_source
        self.encoding = encoding

    def parse(self) -> pd.DataFrame:
        """
        Parse the CSV file and return a clean DataFrame.
        
        This method attempts to read the CSV with intelligent defaults 
        and handles common exceptions gracefully.
        
        Returns:
            A pandas DataFrame with the parsed data.
            
        Raises:
            ValueError: If the file cannot be parsed or is empty.
            FileNotFoundError: If the specified file does not exist.
        """
        try:
            # Attempt to read with common settings
            df = pd.read_csv(
                self.file_source,
                encoding=self.encoding,
                sep=None,  # Auto-detect separator
                engine='python',  # More robust engine
                skip_blank_lines=True,
                header='infer'  # Infer header row
            )
            
            # Remove fully empty rows and columns
            df.dropna(how='all', axis=0, inplace=True)
            df.dropna(how='all', axis=1, inplace=True)
            
            if df.empty:
                raise ValueError("CSV file is empty or contains no data.")
            
            return df

        except FileNotFoundError:
            raise FileNotFoundError(f"The file was not found: {self.file_source}")
        except Exception as e:
            # Catch other potential parsing errors
            raise ValueError(f"Failed to parse CSV file: {e}")

def parse_csv_file(file_source: Union[str, io.BytesIO]) -> pd.DataFrame:
    """
    Convenience function to parse a CSV file directly.
    
    Args:
        file_source: The path to the CSV file or a file-like object.
        
    Returns:
        A pandas DataFrame with the parsed data.
    """
    parser = CSVParser(file_source)
    return parser.parse()
