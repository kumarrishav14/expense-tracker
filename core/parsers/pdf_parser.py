"""
PDF Parser for Bank Statements

This module provides a parser for converting PDF bank statements into a structured pandas DataFrame.
It is designed to handle both standard and password-protected PDF files, extracting tabular data
and relevant text to create a raw, clean dataset for further processing.

Chosen Library: pdfplumber
- It is a pure-Python library with no external dependencies, making it easy to install and deploy.
- It robustly handles text, tables, and encrypted files, making it the ideal choice for this project's requirements.
"""
import io
import pandas as pd
import pdfplumber
from typing import Union, Optional
from pdfminer.pdfdocument import PDFPasswordIncorrect

# Define a specific type for the file source for clarity and correctness.
T_FileSource = Union[str, io.BytesIO]

class PDFParser:
    """
    Parses a PDF file, handling encryption and extracting transaction data.
    
    This class encapsulates the logic for opening, reading, and extracting data
    from a PDF file, returning it as a pandas DataFrame.
    """
    def __init__(self, file_source: T_FileSource, password: Optional[str]):
        """
        Initializes the parser with the file source and an optional password.

        Args:
            file_source: A file path or a standard in-memory binary stream.
            password: The password for an encrypted PDF.
        """
        self.file_source = file_source
        self.password = password

    def parse(self) -> pd.DataFrame:
        """
        Extracts all tables from the PDF and returns a raw DataFrame.

        This method no longer assumes a header row. It concatenates all table
        rows into a single DataFrame with generic column names.

        Returns:
            A raw pandas DataFrame containing all extracted table data.
            
        Raises:
            ValueError: If the password is invalid, the file is corrupted, or no data is found.
        """
        if isinstance(self.file_source, io.BytesIO):
            self.file_source.seek(0)
            
        try:
            with pdfplumber.open(self.file_source, password=self.password) as pdf:
                if not pdf.pages:
                    raise ValueError("PDF is encrypted and requires a password, but none was provided.")

                all_rows = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        all_rows.extend(table)
                
                if not all_rows:
                    raise ValueError("No transaction data could be found in the PDF.")
                
                # Create a raw DataFrame without assuming a header
                df = pd.DataFrame(all_rows)
                df.dropna(how='all', inplace=True)
                
                if df.empty:
                    raise ValueError("No transaction data could be found in the PDF.")
                
                return df

        except PDFPasswordIncorrect:
            raise ValueError("Invalid password provided or PDF is encrypted.")
        except Exception as e:
            raise ValueError(f"Could not parse the PDF file. It may be corrupted: {e}")

def is_pdf_encrypted(file_source: T_FileSource) -> bool:
    """
    Checks if a PDF file is encrypted without performing a full parse.

    Args:
        file_source: A file path or a standard in-memory binary stream.

    Returns:
        True if the PDF is encrypted, False otherwise.
    """
    if isinstance(file_source, io.BytesIO):
        file_source.seek(0)

    try:
        with pdfplumber.open(file_source) as pdf:
            is_encrypted = not pdf.pages
        
        if isinstance(file_source, io.BytesIO):
            file_source.seek(0)
            
        return is_encrypted
    except Exception:
        return True


def parse_pdf(file_source: T_FileSource, password: Optional[str]) -> pd.DataFrame:
    """
    A simple, one-shot function to parse a PDF.
    
    Args:
        file_source: A file path or a standard in-memory binary stream.
        password: The password for an encrypted PDF.
        
    Returns:
        A pandas DataFrame containing the extracted data.
    """
    parser = PDFParser(file_source, password)
    return parser.parse()
