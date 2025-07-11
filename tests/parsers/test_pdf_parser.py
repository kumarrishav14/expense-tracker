"""
Tests for the PDFParser.
"""

import pytest
import pandas as pd
import io
from core.parsers.pdf_parser import PDFParser, is_pdf_encrypted, parse_pdf


def test_parse_unprotected_pdf_from_path(unprotected_pdf_file):
    """Test parsing an unprotected PDF from a file path."""
    parser = PDFParser(unprotected_pdf_file, password=None)
    df = parser.parse()
    assert isinstance(df, pd.DataFrame)
    # The extracted table will have 2 rows and 2 columns
    assert df.shape == (2, 2)
    assert 'Col1' in df.iloc[0].values

def test_parse_unprotected_pdf_from_memory(unprotected_pdf_file):
    """Test parsing an unprotected PDF from an in-memory stream."""
    with open(unprotected_pdf_file, "rb") as f:
        in_memory_file = io.BytesIO(f.read())
    
    parser = PDFParser(in_memory_file, password=None)
    df = parser.parse()
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)

def test_is_pdf_encrypted_unprotected(unprotected_pdf_file):
    """Test that is_pdf_encrypted returns False for an unprotected PDF."""
    assert not is_pdf_encrypted(unprotected_pdf_file)


@pytest.mark.parametrize("password, should_succeed", [("correct_password", True), ("wrong_password", False)])
def test_parse_protected_pdf(protected_pdf_file, mocker, password, should_succeed):
    """Test parsing a protected PDF with correct and incorrect passwords."""
    # Since fpdf doesn't create real passwords, we mock the behavior
    def mock_open(*args, **kwargs):
        if kwargs.get('password') == 'correct_password':
            mock_pdf = mocker.MagicMock()
            mock_page = mocker.MagicMock()
            mock_page.extract_tables.return_value = [[['Secret1', 'Secret2']]]
            mock_pdf.pages = [mock_page]
            # pdfplumber.open returns a context manager
            mock_context_manager = mocker.MagicMock()
            mock_context_manager.__enter__.return_value = mock_pdf
            return mock_context_manager
        else:
            raise ValueError("Invalid password provided or PDF is encrypted.")

    mocker.patch('pdfplumber.open', side_effect=mock_open)

    if should_succeed:
        df = parse_pdf(protected_pdf_file, password=password)
        assert isinstance(df, pd.DataFrame)
        assert 'Secret1' in df.iloc[0].values
    else:
        with pytest.raises(ValueError, match="Invalid password provided or PDF is encrypted."):
            parse_pdf(protected_pdf_file, password=password)

def test_no_data_found_error(empty_pdf_file):
    """Test that a ValueError is raised if no tables are found in the PDF."""
    with pytest.raises(ValueError, match="No transaction data could be found in the PDF."):
        parse_pdf(empty_pdf_file, password=None)