# Data Processor Test Plan

## Overview
This test plan covers the simplified DataProcessor implementation that converts raw bank statement data into standardized DataFrames compatible with db_interface. The tests follow the micro-architecture specification and focus on basic functionality with good coverage for a personal expense tracking app.

## Test Strategy
- **Focus**: Basic functionality with good coverage for personal use
- **Approach**: Unit tests for each method + integration tests for complete pipeline
- **Framework**: pytest with fixtures for test data
- **Coverage**: All public methods and error conditions
- **Scope**: Single-user personal app (simplified testing requirements)

## Test Categories

### 1. Column Mapping Tests (`test_map_columns.py`)
**Purpose**: Verify intelligent column mapping from raw data to standard schema

**Test Cases**:
- **Exact Name Matching**: Standard column names (amount, transaction_date, description)
- **Keyword Matching**: Common variations (debit/credit, date, memo, details)
- **Data Type Detection**: Numeric → amount, datetime → date, string → description
- **Debit/Credit Combination**: Separate debit/credit columns combined into amount
- **Missing Required Fields**: Error handling when required columns cannot be mapped
- **Case Insensitive Matching**: Column names with different cases
- **Extra Columns**: Handling of unmapped columns (should be ignored)

**Key Assertions**:
- Required columns (transaction_date, description, amount) are successfully mapped
- Optional columns (category, sub_category) get default values when missing
- Debit/credit columns are properly combined (credit positive, debit negative)
- ValueError raised when required columns cannot be mapped

### 2. Data Validation and Cleaning Tests (`test_validate_and_clean_data.py`)
**Purpose**: Verify data cleaning and validation operations

**Test Cases**:
- **Date Parsing**: Various date formats (DD/MM/YYYY, MM-DD-YYYY, etc.)
- **Amount Cleaning**: Currency symbols removal, comma handling, numeric conversion
- **Description Cleaning**: Whitespace trimming, empty description handling
- **Invalid Data Removal**: Rows with unparseable dates/amounts are removed
- **Duplicate Removal**: Same date/amount/description duplicates removed
- **Empty DataFrame Handling**: Error when all rows are invalid
- **Data Type Conversion**: String amounts converted to numeric

**Key Assertions**:
- transaction_date column is datetime type
- amount column is numeric type
- Invalid rows are properly removed
- Duplicates are eliminated
- ValueError raised when all data is invalid

### 3. AI Categorization Tests (`test_add_ai_categories_disabled.py`)
**Purpose**: Verify AI categorization structure (DISABLED - AI backend not available)

**Current Status**: DISABLED until AI backend is implemented

**Test Cases** (Currently Commented Out):
- **Keyword Matching**: Descriptions matching category keywords
- **Default Category**: Transactions not matching any keywords get "Other"
- **Existing Categories**: Pre-assigned categories are preserved
- **Sub-category Assignment**: Based on transaction amount (Small/Regular/Large)
- **Case Insensitive Matching**: Keywords work regardless of description case
- **Multiple Keywords**: First matching category is assigned
- **Empty Descriptions**: Handled gracefully

**Current Active Tests**:
- Method existence and structure validation
- Basic column addition without categorization logic

**Key Assertions** (TODO - Enable when AI backend available):
- Correct categories assigned based on description keywords
- Sub-categories assigned based on amount ranges
- Existing categories are not overwritten
- All transactions get a category (default "Other" if no match)

### 4. Integration Tests (`test_integration.py`)
**Purpose**: Test complete processing pipeline end-to-end

**Test Cases**:
- **Complete Pipeline**: Raw DataFrame → Standardized DataFrame
- **Real Bank Statement Formats**: Common CSV/Excel formats from banks
- **Error Recovery**: Partial processing when some rows are invalid
- **Output Schema Validation**: Final DataFrame matches db_interface expectations
- **Processing Summary**: Accurate statistics generation

**Key Assertions**:
- Output DataFrame has exactly the required columns for db_interface
- All required fields are present and valid
- Processing summary provides accurate statistics
- Pipeline handles mixed valid/invalid data gracefully

### 5. Error Handling Tests (`test_error_handling.py`)
**Purpose**: Verify robust error handling and edge cases

**Test Cases**:
- **Empty DataFrame**: Proper error message for empty input
- **No Valid Columns**: Error when no mappable columns found
- **All Invalid Data**: Error when cleaning removes all rows
- **Malformed Data**: Handling of completely corrupted data
- **Missing Required Columns**: Clear error messages for unmappable required fields

**Key Assertions**:
- Appropriate ValueError exceptions with descriptive messages
- Error conditions don't crash the processor
- Partial processing continues when possible

### 6. Basic Functionality Tests (`test_basic_functionality.py`)
**Purpose**: Test core functionality and happy path scenarios

**Test Cases**:
- **Standard Bank Statement**: Typical CSV with standard column names
- **Processing Summary**: Accurate statistics generation
- **Column Preservation**: Only db_interface columns in final output
- **Data Type Consistency**: Proper data types in output DataFrame

**Key Assertions**:
- Successful processing of well-formed data
- Output matches expected schema exactly
- Processing statistics are accurate

## Test Data Strategy

### Sample Data Sets
1. **Standard Format**: Perfect bank statement with standard column names
2. **Variant Formats**: Different column naming conventions
3. **Debit/Credit Format**: Separate debit and credit columns
4. **Messy Data**: Mixed valid/invalid rows, formatting issues
5. **Edge Cases**: Empty descriptions, zero amounts, future dates

### Test Fixtures
- **Raw DataFrames**: Various input formats
- **Expected Outputs**: Standardized DataFrames for comparison
- **Error Cases**: Invalid data that should trigger exceptions

## Coverage Requirements

### Minimum Coverage Targets
- **Overall**: 90%+ line coverage
- **Critical Methods**: 100% coverage for main processing pipeline
- **Error Paths**: All exception conditions tested
- **Edge Cases**: Boundary conditions and unusual inputs

### Coverage Exclusions
- TODO comments and placeholder code
- Defensive assertions that should never execute
- Future AI integration placeholders

## Test Execution Strategy

### Test Organization
```
tests/processors/data_processor/
├── conftest.py                    # Shared fixtures and test data
├── test_basic_functionality.py   # Happy path and core functionality
├── test_map_columns.py           # Column mapping logic
├── test_validate_and_clean_data.py # Data cleaning and validation
├── test_add_ai_categories.py     # Categorization logic
├── test_integration.py           # End-to-end pipeline tests
└── test_error_handling.py        # Error conditions and edge cases
```

### Test Dependencies
- **pytest**: Testing framework
- **pandas**: DataFrame operations and assertions
- **datetime**: Date/time test data generation
- **pytest-cov**: Coverage reporting

### Performance Considerations
- Tests should complete quickly (< 1 second each)
- Use small test datasets (< 100 rows)
- Focus on correctness over performance testing
- No stress testing required for personal app

## Success Criteria

### Functional Requirements
- ✅ All public methods have comprehensive test coverage
- ✅ Error conditions are properly tested and handled
- ✅ Integration tests verify end-to-end functionality
- ✅ Output DataFrame matches db_interface schema exactly

### Quality Requirements
- ✅ 90%+ code coverage achieved
- ✅ All tests pass consistently
- ✅ Clear, descriptive test names and assertions
- ✅ Proper test isolation (no test dependencies)

### Documentation Requirements
- ✅ Test plan documents testing approach
- ✅ Test cases are self-documenting with clear names
- ✅ Complex test logic includes explanatory comments

## Future Considerations

### Phase 2 Enhancements
- Performance testing for larger datasets
- Real AI integration testing (when AI backend available)
- Advanced column mapping scenarios
- Multi-currency support testing

### Maintenance Strategy
- Update tests when DataProcessor functionality changes
- Add regression tests for any bugs discovered
- Keep test data current with real bank statement formats
- Regular review of coverage reports

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-02  
**Test Framework**: pytest  
**Coverage Target**: 90%+  
**Scope**: Personal expense tracking app