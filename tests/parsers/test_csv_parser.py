
"""
Tests for the CSVParser.
"""

import pytest
import pandas as pd
import io
from core.parsers.csv_parser import CSVParser

@pytest.fixture
def sample_csv_content():
    """Provides sample CSV content with empty rows and columns."""
    return '''header1,header2,header3,,header4
data1,data2,data3,,data4

data5,data6,data7,,data8
,,,
'''

@pytest.fixture
def temp_csv_file(tmp_path, sample_csv_content):
    """Creates a temporary CSV file for testing."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(sample_csv_content)
    return str(csv_file)

def test_parse_from_file_path(temp_csv_file):
    """Test that the parser reads from a file path and cleans data."""
    parser = CSVParser(temp_csv_file)
    df = parser.parse()

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 4)  # 2 rows, 4 columns after cleaning
    assert not df.isnull().values.any()
    assert 'header1' in df.columns
    assert 'header4' in df.columns

def test_parse_from_in_memory_object(sample_csv_content):
    """Test that the parser reads from an in-memory object."""
    in_memory_file = io.StringIO(sample_csv_content)
    parser = CSVParser(in_memory_file)
    df = parser.parse()

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 4)
    assert not df.isnull().values.any()
    assert 'data1' in df['header1'].values

def test_file_not_found_error():
    """Test that FileNotFoundError is raised for a non-existent file."""
    with pytest.raises(FileNotFoundError):
        parser = CSVParser("non_existent_file.csv")
        parser.parse()

def test_empty_csv_error():
    """Test that ValueError is raised for an empty CSV."""
    with pytest.raises(ValueError, match="CSV file is empty or contains no data."):
        in_memory_file = io.StringIO(",,\n,")
        parser = CSVParser(in_memory_file)
        parser.parse()
