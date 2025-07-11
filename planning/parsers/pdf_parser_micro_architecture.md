# PDF Parser Micro-Architecture

**Author:** AI Architect
**Date:** July 10, 2025

## 1. Component Overview

The `PDFParser` is a core component in the `core.parsers` module responsible for ingesting PDF bank statements and converting them into a structured pandas DataFrame. This component is designed to handle both password-less and password-protected PDFs, providing a seamless experience as defined in the `pdf_upload_sequence.md` document.

**Chosen Library:** `pdfplumber`
- **Reasoning:** It is a pure-Python library with no external dependencies, making it easy to install and deploy. It robustly handles text, tables, and encrypted files, making it the ideal choice for this project's requirements.

## 2. Position in System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Statement Input Tab (UI)                     │
└─────────────┬───────────────────────────────────────────────────┘
              │ Standard `io.BytesIO` stream (+ optional password)
┌─────────────▼───────────────────────────────────────────────────┐
│                  PDF_PARSER COMPONENT                           │
│  • Encryption Check                                             │
│  • Table & Text Extraction                                      │
│  • Data Structuring                                             │
└─────────────┬───────────────────────────────────────────────────┘
              │ Raw pandas DataFrame
┌─────────────▼───────────────────────────────────────────────────┐
│                  DATA_PROCESSOR COMPONENT                       │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Core Responsibilities

| Responsibility | Description |
|---|---|
| **Encryption Check** | Quickly determine if a PDF is password-protected without a full parse. |
| **Text Extraction** | Extract relevant text data from the PDF, such as transaction descriptions. |
| **Table Extraction** | Identify and extract tabular data representing transactions. |
| **Data Structuring** | Combine extracted text and table data into a single, raw pandas DataFrame. |
| **Error Handling** | Gracefully handle invalid passwords, corrupted files, and parsing failures. |

## 4. Component Architecture

### 4.1. Public Interface

The component will expose a simple class and two convenience functions. The type hints are specific to standard Python types to ensure the parser is decoupled from any web framework.

```python
# In core/parsers/pdf_parser.py
import io
from typing import Union
import pandas as pd
import pdfplumber

# Define a specific type for the file source for clarity and correctness.
T_FileSource = Union[str, io.BytesIO]

class PDFParser:
    """
    Parses a PDF file, handling encryption and extracting transaction data.
    """
    def __init__(self, file_source: T_FileSource, password: str = None):
        """
        Initializes the parser with the file source and an optional password.

        Args:
            file_source: A file path or a standard in-memory binary stream.
            password: The password for an encrypted PDF.
        """
        # ...

    def parse(self) -> pd.DataFrame:
        """
        Extracts tables and relevant text to produce a raw transaction DataFrame.
        """
        # ...

# --- Convenience Functions ---

def is_pdf_encrypted(file_source: T_FileSource) -> bool:
    """
    Checks if a PDF file is encrypted without performing a full parse.

    Args:
        file_source: A file path or a standard in-memory binary stream.
    """
    # ...

def parse_pdf(file_source: T_FileSource, password: str = None) -> pd.DataFrame:
    """
    A simple, one-shot function to parse a PDF.
    """
    parser = PDFParser(file_source, password)
    return parser.parse()

```

### 4.2. Internal Logic

#### `is_pdf_encrypted()`

1.  Accepts a `file_source` (`str` or `io.BytesIO`).
2.  **Important:** If the source is a stream, its position must be reset before and after the check (`file_source.seek(0)`).
3.  Uses a `try...except` block with `pdfplumber.open(file_source)`.
4.  If it raises `pdfplumber.pdfminer.pdfdocument.PDFPasswordIncorrect`, the file is encrypted. Return `True`.
5.  If it succeeds, return `False`.

#### `PDFParser.parse()`

1.  Opens the PDF using `pdfplumber.open(self.file_source, password=self.password)`.
2.  Iterates through each page, extracting tables with `page.extract_tables()` and text with `page.extract_text()`.
3.  Concatenates data from all pages into a unified structure.
4.  Converts the structure into a pandas DataFrame and returns it.

## 5. Error Handling

The parser must handle the following specific error conditions:

| Error Condition | Trigger | Action |
|---|---|---|
| **Invalid Password** | The user provides the wrong password for an encrypted PDF. | Raise a `ValueError` with a user-friendly message like "Invalid password provided." |
| **Corrupted File** | `pdfplumber` fails to open a file that is not password-related. | Raise a `ValueError` with a message like "Could not parse the PDF file. It may be corrupted." |
| **No Data Found** | The PDF is parsed successfully, but no tables or recognizable transaction data are extracted. | Raise a `ValueError` with the message "No transaction data could be found in the PDF." |

## 6. Integration with Frontend Flow

This design directly supports the decoupled sequence defined in `planning/pdf_upload_sequence.md`:

1.  The **Statement Input Tab** receives a Streamlit `UploadedFile` object.
2.  It **converts** the uploaded file into an `io.BytesIO` stream by calling `.getvalue()`.
3.  It first calls `is_pdf_encrypted(stream)`.
4.  If `True`, it prompts the user for a password.
5.  Finally, it calls `parse_pdf(stream, password=user_password)` to get the raw DataFrame, which is then passed to the `DataProcessor`.
