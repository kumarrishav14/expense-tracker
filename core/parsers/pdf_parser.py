"""
PDF Parser for Bank Statements

This module provides a parser for converting PDF bank statements into a structured pandas DataFrame.
It is designed to handle both standard and password-protected PDF files, extracting tabular data
and relevant text to create a raw, clean dataset for further processing.

Chosen Library: pdfplumber
- It is a pure-Python library with no external dependencies, making it easy to install and deploy.
- It robustly handles text, tables, and encrypted files, making it the ideal choice for this project's requirements.
"""

import pandas as pd
import pdfplumber
from typing import Union, IO
from pdfplumber.pdfminer.pdfdocument import PDFPasswordIncorrect

class PDFParser:
    """
    Parses a PDF file, handling encryption and extracting transaction data.
    
    This class encapsulates the logic for opening, reading, and extracting data
    from a PDF file, returning it as a pandas DataFrame.
    """
    def __init__(self, file_source: Union[str, IO], password: str = None):
        """
        Initializes the parser with the file source and an optional password.

        Args:
            file_source: A file path or an in-memory file-like object.
            password: The password for an encrypted PDF.
        """
        self.file_source = file_source
        self.password = password

    def parse(self) -> pd.DataFrame:
        """
        Extracts tables and relevant text to produce a raw transaction DataFrame.

        This method opens the PDF, iterates through its pages, and extracts all
        tables. It then concatenates the data into a single DataFrame.

        Returns:
            A pandas DataFrame containing the extracted data.
            
        Raises:
            ValueError: If the password is invalid, the file is corrupted, or no data is found.
        """
        try:
            with pdfplumber.open(self.file_source, password=self.password) as pdf:
                all_tables = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        all_tables.extend(table)
                
                if not all_tables:
                    raise ValueError("No transaction data could be found in the PDF.")
                
                # Find the header row to use as columns
                header = all_tables[0]
                data = all_tables[1:]
                
                df = pd.DataFrame(data, columns=header)
                df.dropna(how='all', inplace=True) # Clean empty rows
                
                if df.empty:
                    raise ValueError("No transaction data could be found in the PDF.")
                
                return df

        except PDFPasswordIncorrect:
            raise ValueError("Invalid password provided.")
        except Exception as e:
            raise ValueError(f"Could not parse the PDF file. It may be corrupted: {e}")

def is_pdf_encrypted(file_source: Union[str, IO]) -> bool:
    """
    Checks if a PDF file is encrypted without performing a full parse.

    Args:
        file_source: A file path or an in-memory file-like object.

    Returns:
        True if the PDF is encrypted, False otherwise.
    """
    try:
        # The with statement ensures the file is closed
        with pdfplumber.open(file_source) as pdf:
            # Accessing pages will trigger password error if encrypted
            _ = pdf.pages 
        return False
    except PDFPasswordIncorrect:
        return True
    except Exception:
        # Assuming other exceptions mean it's not a password issue
        return False

def parse_pdf(file_source: Union[str, IO], password: str = None) -> pd.DataFrame:
    """
    A simple, one-shot function to parse a PDF.
    
    Args:
        file_source: A file path or an in-memory file-like object.
        password: The password for an encrypted PDF.
        
    Returns:
        A pandas DataFrame containing the extracted data.
    """
    parser = PDFParser(file_source, password)
    return parser.parse()
