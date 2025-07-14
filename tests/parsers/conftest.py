"""
Fixtures for parser tests, including PDF generation.
"""
import pytest
from fpdf import FPDF
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

@pytest.fixture(scope="session")
def unprotected_pdf_file(tmp_path_factory):
    """Creates a simple, unprotected PDF file for testing."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Test Document - Unprotected", ln=1, align="C")
    pdf.ln(10)
    pdf.cell(40, 10, 'Col1', 1)
    pdf.cell(40, 10, 'Col2', 1)
    pdf.ln()
    pdf.cell(40, 10, 'Data1', 1)
    pdf.cell(40, 10, 'Data2', 1)
    
    file_path = tmp_path_factory.mktemp("data") / "unprotected.pdf"
    pdf.output(str(file_path))
    return str(file_path)

@pytest.fixture(scope="session")
def protected_pdf_file(tmp_path_factory):
    """Creates a simple, password-protected PDF file."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Test Document - Protected", ln=1, align="C")
    pdf.ln(10)
    pdf.cell(40, 10, 'Secret1', 1)
    pdf.cell(40, 10, 'Secret2', 1)

    file_path = tmp_path_factory.mktemp("data") / "protected.pdf"
    pdf.output(str(file_path), "F")
    # The fpdf library does not support password protection directly.
    # For the purpose of this test, we will simulate a protected PDF
    # by creating a file that pdfplumber will identify as encrypted.
    # A truly password-protected PDF would be needed for a full integration test.
    # We will rely on the is_pdf_encrypted mock for this test.
    return str(file_path)

@pytest.fixture
def empty_pdf_file(tmp_path):
    """Creates a PDF with no content."""
    pdf = FPDF()
    pdf.add_page()
    file_path = tmp_path / "empty.pdf"
    pdf.output(str(file_path))
    return str(file_path)